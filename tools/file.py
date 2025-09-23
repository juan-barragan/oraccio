
import pandas as pd
# style_this is a set of tuples (index, column)
# Index is in reality a professor and column a day_hour

def dump_to_html(df, history, filename=None):
    """
    Dump the DataFrame to an HTML string, coloring all cells in style_this.
    style_this: set of (index, column) tuples to highlight (index is the DataFrame index, column is the column name)
    If filename is provided, write the HTML to that file.
    """
    style_this = [
        (p, c) for entry in history for p, c in entry
    ]
    html_string = '<table style="width:80%" border="1" cellspacing="0" cellpadding="4">'
    # Identify day boundaries from column names (e.g., LUN8, MAR8, ...)
    day_prefixes = []
    last_prefix = None
    for col in df.columns:
        prefix = ''.join([c for c in col if not c.isdigit()])
        if prefix != last_prefix:
            day_prefixes.append((col, prefix))
            last_prefix = prefix
    # Header
    html_string += "<tr><th>index</th>"
    for i, col in enumerate(df.columns):
        # Add a thicker left border if this column is the first of a new day
        border_style = ""
        for day_col, prefix in day_prefixes:
            if col == day_col:
                border_style = 'border-left: 3px solid black;'
                break
        html_string += f'<th style="{border_style}">{col}</th>'
    html_string += "</tr>"
    # Rows
    for idx in df.index:
        html_string += f"<tr><td>{idx}</td>"
        for i, col in enumerate(df.columns):
            value = df.loc[idx, col]
            # Add a thicker left border if this column is the first of a new day
            border_style = ""
            for day_col, prefix in day_prefixes:
                if col == day_col:
                    border_style = 'border-left: 3px solid black;'
                    break
            if (idx, col) in style_this:
                html_string += f'<td style="background-color:Orange;{border_style}">{value if pd.notnull(value) else ""}</td>'
            else:
                html_string += f'<td style="{border_style}">{value if pd.notnull(value) else ""}</td>'
        html_string += "</tr>"
    html_string += "</table>"
    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_string)
    return html_string

def wite_to_html_file(html, filename):
    with open(filename, "w") as f:
        f.write(html)