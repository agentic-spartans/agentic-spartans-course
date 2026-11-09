-- Size each table column to its content. Pandoc otherwise splits the page
-- width equally, and LibreOffice keeps that split in the PDF.
local LINE = 80 -- characters that fit across the page
local CAP = 50  -- a longer cell wraps instead of widening its column further

local function length(s)
  return utf8.len(s) or #s
end

function Table(tbl)
  local n = #tbl.colspecs
  local width = {}
  for i = 1, n do width[i] = 1 end

  -- Row spans keep their columns occupied in the rows below. A cell that
  -- spans several columns is sized after the others, over its columns.
  local spans = {}
  local function measure(rows)
    local busy = {}
    for _, row in ipairs(rows) do
      local col = 1
      for _, cell in ipairs(row.cells) do
        while (busy[col] or 0) > 0 do col = col + 1 end
        if col > n then break end
        local span = cell.col_span or 1
        local text = pandoc.utils.stringify(cell.contents)
        local need = math.min(length(text), CAP)
        for word in text:gmatch("%S+") do need = math.max(need, length(word)) end
        span = math.min(span, n - col + 1)
        if span == 1 then
          width[col] = math.max(width[col], need)
        else
          spans[#spans + 1] = {col = col, span = span, need = need}
        end
        for c = col, col + span - 1 do busy[c] = cell.row_span or 1 end
        col = col + span
      end
      for c = 1, n do
        if (busy[c] or 0) > 0 then busy[c] = busy[c] - 1 end
      end
    end
  end

  measure(tbl.head.rows)
  for _, body in ipairs(tbl.bodies) do
    measure(body.head)
    measure(body.body)
  end
  measure(tbl.foot.rows)

  for _, s in ipairs(spans) do
    local have = -4
    for c = s.col, s.col + s.span - 1 do have = have + width[c] + 4 end
    if have < s.need then
      for c = s.col, s.col + s.span - 1 do
        width[c] = width[c] + (s.need - have) / s.span
      end
    end
  end

  local total = 0
  for i = 1, n do total = total + width[i] + 4 end
  local scale = math.max(total, LINE)
  for i = 1, n do
    tbl.colspecs[i] = {tbl.colspecs[i][1], (width[i] + 4) / scale}
  end
  return tbl
end
