import csv, hashlib, json
from pathlib import Path
import pandas as pd
import pytest
from as_report.input_contract import inspect_csv, DATE_FORMATS
from as_report.loader import load_input, REQUIRED_COLUMNS, DataLoadError

def make(tmp_path, headers, rows):
    p=tmp_path/'qa.csv'
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(rows)
    return p

@pytest.mark.parametrize('value,valid', [
 ('2024-02-29',True),('2023-02-29',False),('2000-02-29',True),('1900-02-29',False),
 ('2026-04-31',False),('2026-12-31 23:59:59',True),('2026-12-31 24:00:00',False),
 ('2026-01-01T00:00:00',True),('2026-01-01T00:00:00Z',False),('45292',False),
 ('01/02/2026',False),('2026-00-01',False),('2026-01-00',False),('9999-12-31',True),
 ('0001-01-01',True),('2026.09.14 09:10',True),(' 2026-09-14 ',True)])
def test_date_boundaries(tmp_path,value,valid):
    p=make(tmp_path,['접수일'],[[value],[' '],['invalid']]); r=inspect_csv(p)
    assert r.rows[0].date_state == ('valid' if valid else 'invalid')
    assert r.rows[0].raw_values[0]==value
    assert sum(r.date_summary[k] for k in ['valid','invalid','missing','unassessed'])==3

@pytest.mark.parametrize('mode',['legacy','alias','both','neither'])
def test_legacy_compatibility_and_no_mutation(tmp_path,mode):
    h=list(REQUIRED_COLUMNS)
    if mode=='alias': h[h.index('고장원인')]='고장유형'
    if mode=='both': h.append('고장유형')
    if mode=='neither': h.remove('고장원인')
    values={k:'value' for k in h}; values.update({'*ID':'001','접수일':'2026-09-14','고장원인':'canonical','고장유형':'alias'})
    p=make(tmp_path,h,[[values[k] for k in h]])
    before=p.read_bytes()
    if mode=='neither':
        with pytest.raises(DataLoadError): load_input(p)
        assert '고장원인' not in inspect_csv(p).field_mapping
        with pytest.raises(DataLoadError): load_input(p)
    else:
        legacy=load_input(p).dataframe
        r=inspect_csv(p)
        pd.testing.assert_frame_equal(legacy,load_input(p).dataframe)
        assert len(legacy)==r.row_count==1
        assert legacy['고장원인'].iloc[0]==('alias' if mode=='alias' else 'canonical')
        assert r.rows[0].original_id=='001'
    assert p.read_bytes()==before

@pytest.mark.parametrize('rows',[[['2026-01-01']], [['2026-01-01','001','extra']], [[]]])
def test_width_error_fails_closed(tmp_path,rows):
    r=inspect_csv(make(tmp_path,['접수일','*ID'],rows))
    assert 'row_width_mismatch' in r.structural_errors
    assert not r.field_mapping
    assert r.date_summary['unassessed']==r.row_count
    assert all(x['usable_rows'] is None and x['status']=='unavailable' for x in r.features.values())
    assert all(x.date_state=='structure_unavailable' for x in r.rows)

def test_multiline_crlf_header_and_json(tmp_path):
    r=inspect_csv(make(tmp_path,['접수일','*ID','extra\r\nheader'],[['2026-09-14','NULL','a\r\nb'],['','000','last']]))
    assert (r.rows[0].line_start,r.rows[0].line_end,r.rows[1].line_start)==(3,4,5)
    assert r.rows[0].original_id=='NULL'
    assert json.loads(json.dumps(r.to_dict(),ensure_ascii=False))['row_count']==2

def test_feature_intersection_and_missing(tmp_path):
    r=inspect_csv(make(tmp_path,['접수일','업무유형','제조사','상태','접수 내용 (요약)'],[
      ['2026-09-14','any','maker','전달 완료','text'], ['bad','any','maker','처리완료','text'],
      ['2026-09-14','any','','',''], ['2026-09-14','','maker','','text']]))
    assert r.features['period_records']['usable_rows']==3
    assert r.features['claim_manufacturer_review']['usable_rows']==1
    assert r.features['follow_up_evidence']['usable_rows']==2
    assert r.features['customer_distribution']['usable_rows'] is None
    assert r.field_summary['상태']['missing']==2

@pytest.mark.parametrize('size',[131071,131072,131073])
def test_valid_long_text_preserved(tmp_path,size):
    value='가'*size
    p=make(tmp_path,['접수일','접수 내용 (자세히)'],[['2026-09-14',value]])
    r=inspect_csv(p)
    assert r.rows[0].raw_values[1]==value
    assert r.features['follow_up_evidence']['usable_rows']==1
