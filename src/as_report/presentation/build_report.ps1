param(
    [Parameter(Mandatory = $true)][string]$TemplatePath,
    [Parameter(Mandatory = $true)][string]$PayloadPath,
    [Parameter(Mandatory = $true)][string]$PptxOutputPath,
    [Parameter(Mandatory = $true)][string]$PdfOutputPath,
    [switch]$SkipPdf
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Rgb([int]$r, [int]$g, [int]$b) {
    return $r + (256 * $g) + (65536 * $b)
}

$Blue = Rgb 0 91 159
$BlueLight = Rgb 225 239 249
$Navy = Rgb 18 59 104
$Teal = Rgb 27 126 116
$TealLight = Rgb 226 244 241
$Gray900 = Rgb 36 49 61
$Gray700 = Rgb 75 90 103
$Gray500 = Rgb 132 145 155
$Gray300 = Rgb 218 225 230
$Gray100 = Rgb 246 248 250
$White = Rgb 255 255 255
$Amber = Rgb 226 147 26
$Red = Rgb 195 61 61

$FontName = "맑은 고딕"
$SlideWidth = 960
$SlideHeight = 540

function Find-Layout($presentation, [string]$name) {
    foreach ($master in $presentation.Designs) {
        foreach ($layout in $master.SlideMaster.CustomLayouts) {
            if ($layout.Name -eq $name) { return $layout }
        }
    }
    throw "PPT layout not found: $name"
}

function Clear-Placeholders($slide) {
    for ($i = $slide.Shapes.Count; $i -ge 1; $i--) {
        $shape = $slide.Shapes.Item($i)
        if ($shape.Type -eq 14) { $shape.Delete() }
    }
}

function Add-Text($slide, [string]$text, [double]$left, [double]$top, [double]$width, [double]$height, [double]$size = 16, [int]$color = $Gray900, [bool]$bold = $false, [int]$align = 1) {
    $shape = $slide.Shapes.AddTextbox(1, $left, $top, $width, $height)
    $shape.TextFrame.MarginLeft = 0
    $shape.TextFrame.MarginRight = 0
    $shape.TextFrame.MarginTop = 0
    $shape.TextFrame.MarginBottom = 0
    $shape.TextFrame.WordWrap = -1
    $shape.TextFrame.TextRange.Text = $text
    $shape.TextFrame.TextRange.Font.Name = $FontName
    $shape.TextFrame.TextRange.Font.Size = $size
    $shape.TextFrame.TextRange.Font.Bold = $(if ($bold) { -1 } else { 0 })
    $shape.TextFrame.TextRange.Font.Color.RGB = $color
    $shape.TextFrame.TextRange.ParagraphFormat.Alignment = $align
    return $shape
}

function Add-Rect($slide, [double]$left, [double]$top, [double]$width, [double]$height, [int]$fill, [int]$line = $fill, [double]$radius = 0) {
    $shapeType = $(if ($radius -gt 0) { 5 } else { 1 })
    $shape = $slide.Shapes.AddShape($shapeType, $left, $top, $width, $height)
    $shape.Fill.ForeColor.RGB = $fill
    $shape.Line.ForeColor.RGB = $line
    return $shape
}

function Add-Title($slide, [string]$title, [string]$eyebrow = "A/S ANALYSIS") {
    Add-Text $slide $eyebrow 48 24 250 16 8 $Blue $true | Out-Null
    Add-Text $slide $title 48 43 800 34 25 $Navy $true | Out-Null
    $rule = Add-Rect $slide 48 83 864 2 $Blue $Blue
    $rule.Line.Visible = 0
}

function Add-Empty($slide, [string]$message, [double]$left, [double]$top, [double]$width, [double]$height) {
    $box = Add-Rect $slide $left $top $width $height $Gray100 $Gray300 4
    $box.Fill.Transparency = 0
    Add-Text $slide $message ($left + 18) ($top + ($height / 2) - 10) ($width - 36) 24 13 $Gray500 $false 2 | Out-Null
}

function Convert-Number($value) {
    $number = 0.0
    if ([double]::TryParse([string]$value, [ref]$number)) { return $number }
    return 0.0
}

function Get-Value($row, [string]$key) {
    if ($null -eq $row) { return "" }
    $property = $row.PSObject.Properties[$key]
    if ($null -eq $property -or $null -eq $property.Value) { return "" }
    return [string]$property.Value
}

function Add-KpiCards($slide, $items, [double]$top = 108) {
    $values = @($items)
    $count = [Math]::Min($values.Count, 6)
    if ($count -eq 0) { Add-Empty $slide "표시할 핵심 지표가 없습니다." 48 $top 864 92; return }
    $gap = 10
    $cardWidth = (864 - (($count - 1) * $gap)) / $count
    for ($i = 0; $i -lt $count; $i++) {
        $x = 48 + ($i * ($cardWidth + $gap))
        $card = Add-Rect $slide $x $top $cardWidth 88 $White $Gray300 4
        $card.Shadow.Visible = 0
        Add-Rect $slide $x $top 4 88 $Blue $Blue | Out-Null
        Add-Text $slide ([string]$values[$i].label) ($x + 14) ($top + 14) ($cardWidth - 26) 18 10 $Gray700 $false | Out-Null
        $display = "{0}{1}" -f $values[$i].value, $values[$i].unit
        Add-Text $slide $display ($x + 14) ($top + 40) ($cardWidth - 26) 32 22 $Navy $true | Out-Null
    }
}

function Add-BarChart($slide, [string]$title, $rows, [string]$labelKey, [string]$valueKey, [double]$left, [double]$top, [double]$width, [double]$height, [int]$color = $Blue) {
    Add-Text $slide $title $left $top $width 23 14 $Gray900 $true | Out-Null
    $items = @($rows)
    if ($items.Count -eq 0) { Add-Empty $slide "표시할 데이터가 없습니다." $left ($top + 30) $width ($height - 30); return }
    $maxValue = 0.0
    foreach ($row in $items) { $maxValue = [Math]::Max($maxValue, (Convert-Number (Get-Value $row $valueKey))) }
    if ($maxValue -le 0) { Add-Empty $slide "표시할 데이터가 없습니다." $left ($top + 30) $width ($height - 30); return }
    $visible = [Math]::Min($items.Count, 8)
    $rowHeight = ($height - 42) / $visible
    $labelWidth = [Math]::Min(145, $width * 0.36)
    $barWidth = $width - $labelWidth - 48
    for ($i = 0; $i -lt $visible; $i++) {
        $row = $items[$i]
        $y = $top + 32 + ($i * $rowHeight)
        $label = Get-Value $row $labelKey
        if ($label.Length -gt 18) { $label = $label.Substring(0, 17) + "…" }
        $value = Convert-Number (Get-Value $row $valueKey)
        Add-Text $slide $label $left $y $labelWidth ($rowHeight - 2) 9 $Gray700 $false | Out-Null
        Add-Rect $slide ($left + $labelWidth) ($y + 3) $barWidth 11 $Gray100 $Gray100 | Out-Null
        $filled = [Math]::Max(2, $barWidth * ($value / $maxValue))
        Add-Rect $slide ($left + $labelWidth) ($y + 3) $filled 11 $color $color | Out-Null
        Add-Text $slide ([string]$value) ($left + $labelWidth + $barWidth + 7) ($y - 1) 38 18 9 $Gray900 $true | Out-Null
    }
}

function Add-LineChart($slide, [string]$title, $rows, [string]$labelKey, [string]$valueKey, [double]$left, [double]$top, [double]$width, [double]$height, [int]$color = $Blue) {
    Add-Text $slide $title $left $top $width 23 14 $Gray900 $true | Out-Null
    $items = @($rows)
    if ($items.Count -lt 2) { Add-Empty $slide "추이를 표시할 데이터가 부족합니다." $left ($top + 30) $width ($height - 30); return }
    $maxValue = 0.0
    foreach ($row in $items) { $maxValue = [Math]::Max($maxValue, (Convert-Number (Get-Value $row $valueKey))) }
    if ($maxValue -le 0) { Add-Empty $slide "표시할 데이터가 없습니다." $left ($top + 30) $width ($height - 30); return }
    $plotLeft = $left + 32
    $plotTop = $top + 36
    $plotWidth = $width - 48
    $plotHeight = $height - 74
    Add-Rect $slide $plotLeft ($plotTop + $plotHeight) $plotWidth 1 $Gray300 $Gray300 | Out-Null
    $step = $plotWidth / ($items.Count - 1)
    $lastX = $null
    $lastY = $null
    for ($i = 0; $i -lt $items.Count; $i++) {
        $value = Convert-Number (Get-Value $items[$i] $valueKey)
        $x = $plotLeft + ($i * $step)
        $y = $plotTop + $plotHeight - (($value / $maxValue) * ($plotHeight - 8))
        if ($null -ne $lastX) {
            $line = $slide.Shapes.AddLine($lastX, $lastY, $x, $y)
            $line.Line.ForeColor.RGB = $color
            $line.Line.Weight = 2.4
        }
        $dot = $slide.Shapes.AddShape(9, ($x - 3.5), ($y - 3.5), 7, 7)
        $dot.Fill.ForeColor.RGB = $White
        $dot.Line.ForeColor.RGB = $color
        $dot.Line.Weight = 1.8
        $label = Get-Value $items[$i] $labelKey
        Add-Text $slide $label ($x - 28) ($plotTop + $plotHeight + 7) 56 16 8 $Gray500 $false 2 | Out-Null
        if ($i -eq $items.Count - 1 -or $i -eq 0 -or $value -eq $maxValue) {
            Add-Text $slide ([string]$value) ($x - 22) ($y - 21) 44 15 8 $Gray900 $true 2 | Out-Null
        }
        $lastX = $x
        $lastY = $y
    }
}

function Add-Table($slide, [string]$title, $rows, [string[]]$columns, [string[]]$headers, [double]$left, [double]$top, [double]$width, [double]$height) {
    Add-Text $slide $title $left $top $width 23 14 $Gray900 $true | Out-Null
    $items = @($rows)
    if ($items.Count -eq 0) { Add-Empty $slide "표시할 데이터가 없습니다." $left ($top + 30) $width ($height - 30); return }
    $visible = [Math]::Min($items.Count, 6)
    $tableShape = $slide.Shapes.AddTable($visible + 1, $columns.Count, $left, ($top + 30), $width, ($height - 30))
    $table = $tableShape.Table
    $rowHeight = ($height - 30) / ($visible + 1)
    for ($rowIndex = 1; $rowIndex -le ($visible + 1); $rowIndex++) {
        $table.Rows.Item($rowIndex).Height = $rowHeight
    }
    for ($c = 1; $c -le $columns.Count; $c++) {
        $cell = $table.Cell(1, $c).Shape
        $cell.Fill.ForeColor.RGB = $Navy
        $cell.TextFrame.TextRange.Text = $headers[$c - 1]
        $cell.TextFrame.TextRange.Font.Name = $FontName
        $cell.TextFrame.TextRange.Font.Size = 9
        $cell.TextFrame.TextRange.Font.Bold = -1
        $cell.TextFrame.TextRange.Font.Color.RGB = $White
    }
    for ($r = 0; $r -lt $visible; $r++) {
        for ($c = 1; $c -le $columns.Count; $c++) {
            $cell = $table.Cell($r + 2, $c).Shape
            $cell.Fill.ForeColor.RGB = $(if (($r % 2) -eq 0) { $White } else { $Gray100 })
            $text = Get-Value $items[$r] $columns[$c - 1]
            if ($text.Length -gt 30) { $text = $text.Substring(0, 29) + "…" }
            $cell.TextFrame.TextRange.Text = $text
            $cell.TextFrame.TextRange.Font.Name = $FontName
            $cell.TextFrame.TextRange.Font.Size = 8
            $cell.TextFrame.TextRange.Font.Color.RGB = $Gray900
            $cell.TextFrame.MarginLeft = 4
            $cell.TextFrame.MarginRight = 4
            $cell.TextFrame.MarginTop = 2
            $cell.TextFrame.MarginBottom = 2
        }
    }
}

function Add-Notes($slide, [string]$text) {
    try {
        $notes = $slide.NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange
        $notes.Text = $text
    } catch { }
}

function Add-PageNumber($slide, [int]$number) {
    Add-Text $slide ("{0:00}" -f $number) 864 507 48 14 8 $Gray500 $false 3 | Out-Null
}

function Add-WorkTypeSlide($slide, $detail, [int]$accent) {
    Add-Title $slide $detail.slide_title
    Add-KpiCards $slide $detail.kpis 104
    Add-LineChart $slide "월별 접수 건수" $detail.monthly "기간_연월" "접수 건수" 48 220 540 260 $accent
    Add-BarChart $slide "주요 고객사" $detail.customers "고객사" "접수 건수" 620 220 292 260 $Teal
}

$data = Get-Content -LiteralPath $PayloadPath -Raw -Encoding UTF8 | ConvertFrom-Json
$ppt = New-Object -ComObject PowerPoint.Application
$presentation = $null
try {
    # PowerPoint does not allow Application.Visible to be set to false.
    # Opening the presentation with WithWindow=false keeps the document window hidden.
    $ppt.DisplayAlerts = 1
    $presentation = $ppt.Presentations.Open($TemplatePath, $false, $false, $false)
    while ($presentation.Slides.Count -gt 0) { $presentation.Slides.Item(1).Delete() }
    $coverLayout = Find-Layout $presentation "Cover"
    $contentLayout = Find-Layout $presentation "자유형"

    $slide = $presentation.Slides.AddSlide(1, $coverLayout)
    Clear-Placeholders $slide
    Add-Text $slide $data.title 295 170 600 55 31 $Navy $true | Out-Null
    Add-Text $slide $data.period_label 295 236 500 32 20 $Blue $true | Out-Null
    Add-Text $slide $data.period_range 295 274 500 24 12 $Gray700 $false | Out-Null
    Add-Text $slide ("필터: " + $data.filter_summary) 295 305 570 22 11 $Gray500 $false | Out-Null
    Add-Text $slide ("생성: " + $data.created_at) 295 421 500 18 9 $Gray500 $false | Out-Null
    Add-PageNumber $slide 1
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(2, $contentLayout)
    Clear-Placeholders $slide
    Add-Title $slide "목차"
    Add-Text $slide "01  A/S 종합 현황" 72 125 600 28 18 $Navy $true | Out-Null
    Add-Text $slide "02  월별 접수 및 처리 추이" 72 172 600 28 18 $Navy $true | Out-Null
    Add-Text $slide "03  고객사·업무유형별 접수 현황" 72 219 600 28 18 $Navy $true | Out-Null
    Add-Text $slide "04  설비·부품별 접수 현황" 72 266 600 28 18 $Navy $true | Out-Null
    Add-Text $slide "05  업무유형별 상세 현황" 72 313 600 28 18 $Navy $true | Out-Null
    Add-Text $slide "06  부품 수리·클레임 / VOC 및 기타" 72 360 700 28 18 $Navy $true | Out-Null
    Add-PageNumber $slide 2
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(3, $contentLayout)
    Clear-Placeholders $slide
    Add-Title $slide "A/S 종합 현황"
    Add-KpiCards $slide $data.kpis 104
    Add-Text $slide "핵심 요약" 48 220 420 24 14 $Gray900 $true | Out-Null
    $y = 254
    foreach ($line in @($data.narrative)) {
        Add-Rect $slide 50 ($y + 5) 6 6 $Teal $Teal | Out-Null
        Add-Text $slide ([string]$line) 66 $y 826 34 12 $Gray700 $false | Out-Null
        $y += 42
    }
    Add-PageNumber $slide 3
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(4, $contentLayout)
    Clear-Placeholders $slide
    Add-Title $slide "월별 접수 및 처리 추이"
    Add-LineChart $slide "월별 접수 건수" $data.monthly "기간_연월" "접수 건수" 48 105 540 350 $Blue
    Add-LineChart $slide "월별 처리 완료율" $data.monthly_completion "기간_연월" "처리완료율" 620 105 292 350 $Teal
    Add-PageNumber $slide 4
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(5, $contentLayout)
    Clear-Placeholders $slide
    Add-Title $slide "고객사·업무유형별 접수 현황"
    Add-BarChart $slide "접수 건수 상위 10개 고객사" $data.customers "고객사" "접수 건수" 48 105 420 350 $Blue
    Add-BarChart $slide "업무유형별 접수 건수" $data.work_types "업무유형구분" "접수 건수" 500 105 412 350 $Teal
    Add-PageNumber $slide 5
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(6, $contentLayout)
    Clear-Placeholders $slide
    Add-Title $slide "설비·부품별 접수 현황"
    Add-BarChart $slide "대분류별 접수 건수" $data.categories "대분류" "접수 건수" 48 105 420 350 $Blue
    Add-BarChart $slide "접수 건수 상위 10개 고장부품" $data.parts "소분류 (고장부품)" "접수 건수" 500 105 412 350 $Teal
    Add-PageNumber $slide 6
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(7, $contentLayout)
    Clear-Placeholders $slide
    Add-WorkTypeSlide $slide $data.work_type_details.emergency $Blue
    Add-PageNumber $slide 7
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(8, $contentLayout)
    Clear-Placeholders $slide
    Add-WorkTypeSlide $slide $data.work_type_details.general $Teal
    Add-PageNumber $slide 8
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(9, $contentLayout)
    Clear-Placeholders $slide
    Add-WorkTypeSlide $slide $data.work_type_details.remote $Blue
    Add-PageNumber $slide 9
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(10, $contentLayout)
    Clear-Placeholders $slide
    Add-Title $slide $data.work_type_details.claim.slide_title
    Add-KpiCards $slide $data.work_type_details.claim.kpis 104
    Add-LineChart $slide "월별 접수 건수" $data.work_type_details.claim.monthly "기간_연월" "접수 건수" 48 220 540 260 $Teal
    Add-BarChart $slide "제조사별 접수 건수" $data.manufacturers "제조사" "접수 건수" 620 220 292 260 $Teal
    Add-PageNumber $slide 10
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $slide = $presentation.Slides.AddSlide(11, $contentLayout)
    Clear-Placeholders $slide
    Add-Title $slide "VOC 및 기타 접수 현황"
    Add-Text $slide $data.other_description 48 91 864 20 9 $Gray700 $false | Out-Null
    $vocOtherRows = @($data.work_type_details.voc, $data.work_type_details.other) | ForEach-Object {
        [PSCustomObject]@{
            "업무유형" = $_.display_label
            "접수 건수" = $_.received
            "전체 비중" = $_.share
            "처리완료 건수" = $_.completed
            "미완료 건수" = $_.incomplete
            "처리완료율" = $_.completion_rate
        }
    }
    Add-Table $slide "유형별 접수 현황" $vocOtherRows @("업무유형", "접수 건수", "전체 비중", "처리완료 건수", "미완료 건수", "처리완료율") @("업무유형", "접수", "비중", "처리 완료", "미완료", "처리 완료율") 48 125 864 125
    Add-BarChart $slide "VOC 주요 고객사" $data.work_type_details.voc.customers "고객사" "접수 건수" 48 270 420 205 $Blue
    Add-BarChart $slide "기타 주요 고객사" $data.work_type_details.other.customers "고객사" "접수 건수" 500 270 412 205 $Teal
    Add-PageNumber $slide 11
    Add-Notes $slide "[Sources]`n- A/S analysis input: user-provided internal issue data`n[/Sources]"

    $presentation.SaveAs($PptxOutputPath, 24)
    if (-not $SkipPdf) { $presentation.SaveAs($PdfOutputPath, 32) }
    $presentation.Close()
    $presentation = $null
} finally {
    if ($null -ne $presentation) { try { $presentation.Close() } catch { } }
    $ppt.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($ppt)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
