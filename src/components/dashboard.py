from fasthtml.common import *
from src.components.filter_controls import checklist_filter


def dashboard_page(data: dict):
    summary = Section(
        Div(
            P("This Month", cls="text-xs uppercase tracking-wider cc-subtle"),
            P(data["this_month_expenses"], cls="text-2xl font-semibold text-base-content"),
            P(data["this_month_expenses_projection"], cls="text-xs cc-muted"),
            data_testid="stat-this-month",
            cls="cc-glass rounded-xl p-4 space-y-1",
        ),
        Div(
            P("Selected Expenses", cls="text-xs uppercase tracking-wider cc-subtle"),
            P(data["selected_expenses"], cls="text-2xl font-semibold text-base-content"),
            P(data["selected_expenses_projection"], cls="text-xs cc-muted"),
            data_testid="stat-selected-expenses",
            cls="cc-glass rounded-xl p-4 space-y-1",
        ),
        Div(
            P("Monthly Avg", cls="text-xs uppercase tracking-wider cc-subtle"),
            P(data["avg_monthly_expenses"], cls="text-2xl font-semibold text-base-content"),
            P(data["avg_monthly_expenses_projection"], cls="text-xs cc-muted"),
            cls="cc-glass rounded-xl p-4 space-y-1",
        ),
        Div(
            P("Net Worth", cls="text-xs uppercase tracking-wider cc-subtle"),
            P(data["current_net_worth"], cls="text-2xl font-semibold text-base-content"),
            cls="cc-glass rounded-xl p-4 space-y-1",
        ),
        data_testid="summary-stats",
        cls="grid grid-cols-2 md:grid-cols-4 gap-4",
    )

    if data.get("expense_bars"):
        bar_divs = []
        expense_bars = data["expense_bars"]
        for bar in expense_bars:
            segments = [
                Div(
                    style=f"{segment['height_style']}; background:{segment['color']}",
                    aria_label=f"{bar['month']} {segment['label']} {segment['value_fmt']}",
                    data_expense_segment_label=segment["label"],
                    data_expense_segment_value=segment["value_fmt"],
                    cls="w-full opacity-85 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100",
                )
                for segment in bar["segments"]
            ]
            bar_divs.append(
                Div(
                    _stacked_bar_tooltip(
                        bar,
                        bar["amt_fmt"],
                        "expense-month-tooltip",
                    ),
                    Span(
                        bar["total_compact"],
                        title=bar["amt_fmt"],
                        style=bar["total_position_style"],
                        data_bar_total_label=bar["total_compact"],
                        cls="pointer-events-none absolute left-0 z-20 mb-1 w-full truncate text-center text-[9px] font-medium leading-none tabular-nums text-base-content/70",
                    ),
                    Div(*segments, cls="flex h-full w-full flex-col-reverse justify-start overflow-hidden rounded-t"),
                    tabindex="0",
                    aria_label=f"{bar['month']} expenses {bar['amt_fmt']}",
                    data_expense_total=bar["amt_fmt"],
                    data_cc_stacked_bar="true",
                    cls="group flex-1 flex flex-col items-end justify-end relative h-full focus:outline-none",
                )
            )
        month_labels = [Div(m, cls="flex-1 truncate text-center text-xs cc-subtle") for m in data["expense_months"]]
        bars_section = Div(
            Div(
                Div(
                    Div(
                        _year_marker_overlay(data.get("expense_year_markers") or [], "expense-year-markers", "h-36"),
                        Div(*bar_divs, cls="relative z-10 flex items-end gap-1 h-36"),
                        _expense_trailing_average_overlay(data),
                        cls="relative",
                    ),
                    Div(*month_labels, cls="flex gap-1 mt-1"),
                    style=data["expense_chart_width_style"],
                    cls="cc-chart-canvas",
                ),
                data_testid="expense-chart-scroll",
                cls="cc-chart-scroll",
            ),
            Div(
                *[
                    Div(
                        Span(cls="inline-block h-2 w-5 rounded", style=f"background:{item['color']}"),
                        Span(item["label"], cls="text-xs cc-muted"),
                        cls="flex items-center gap-2",
                    )
                    for item in data.get("expense_chart_legend") or []
                ],
                Span(cls="inline-block h-0.5 w-6 rounded bg-warning"),
                Span("12-month avg", cls="text-xs cc-muted"),
                cls="mt-3 flex flex-wrap items-center gap-3",
            ),
            cls="cc-chart-card cc-glass min-w-0 rounded-xl p-4",
        )
    else:
        bars_section = P("No expense data yet. Add some transactions to see your spending trends.", cls="text-sm cc-muted")

    cat_table = ""
    if data.get("cat_month_rows"):
        header_cells = [Th("Category", cls="px-4 py-2 text-left font-medium cc-muted")]
        for month in data["cat_months"]:
            header_cells.append(Th(month, cls="px-3 py-2 text-right font-medium cc-muted"))
        header_cells.append(Th("Total", cls="px-4 py-2 text-right font-medium cc-muted"))

        body_rows = []
        for row in data["cat_month_rows"]:
            cells = [Td(row["category"], cls="px-4 py-2 text-base-content")]
            for total in row["totals"]:
                cells.append(Td(total, cls="px-3 py-2 text-right cc-muted"))
            cells.append(Td(row["total"], cls="px-4 py-2 text-right font-medium text-base-content"))
            body_rows.append(Tr(*cells, cls="border-b border-base-300/70 hover:bg-base-200/60"))

        cat_table = Div(
            Table(
                Thead(Tr(*header_cells, cls="border-b border-base-300")),
                Tbody(*body_rows),
                cls="table w-full text-sm",
            ),
            cls="cc-glass overflow-x-auto rounded-xl",
        )

    expenses_section = Section(
        H2("Expenses", cls="text-xl font-semibold text-base-content"),
        bars_section,
        cat_table,
        data_testid="expenses-section",
        cls="min-w-0 space-y-4",
    )

    nw_section = Section(
        H2("Net Worth", cls="text-xl font-semibold text-base-content"),
        _net_worth_chart(data),
        _net_worth_table(data),
        data_testid="net-worth-section",
        cls="min-w-0 space-y-4",
    )

    return Div(
        Header(
            Div(
                H1("Dashboard", cls="cc-page-title text-4xl font-semibold text-base-content"),
                Button(
                    "Filters",
                    type="button",
                    data_testid="dashboard-filter-trigger",
                    onclick="document.getElementById('dashboard-filter-overlay')?.classList.add('cc-open')",
                    cls="btn btn-sm btn-primary",
                ),
                cls="flex items-center justify-between gap-4",
            ),
            _dashboard_filters(data),
            cls="space-y-2",
        ),
        summary,
        expenses_section,
        nw_section,
        _stacked_bar_tooltip_behavior(),
        cls="cc-dashboard flex min-w-0 max-w-full flex-col gap-10",
    )


def _dashboard_filters(data: dict):
    filters = data["filters"]
    category_ids = set(filters.category_ids)
    expense_account_ids = set(filters.expense_account_ids)
    net_worth_account_ids = set(filters.net_worth_account_ids)

    date_fields_cls = "grid grid-cols-1 sm:grid-cols-2 gap-3"
    if filters.date_preset != "custom":
        date_fields_cls = f"{date_fields_cls} hidden"

    return Div(
        Div(cls="cc-dashboard-filter-backdrop"),
        Form(
            Div(
                H2("Dashboard Filters", cls="text-lg font-semibold text-base-content"),
                Button(
                    "Close",
                    type="button",
                    onclick="document.getElementById('dashboard-filter-overlay')?.classList.remove('cc-open')",
                    cls="btn btn-sm btn-ghost",
                ),
                cls="flex items-center justify-between gap-4 px-5 py-4 border-b border-base-300/70",
            ),
            Div(
                Label(
                    Span("Range", cls="text-xs font-medium cc-muted"),
                    Select(
                        *_select_options(data["date_presets"], filters.date_preset),
                        name="date_preset",
                        data_dashboard_date_preset="true",
                        cls="select select-bordered select-sm w-full",
                    ),
                    cls="form-control",
                ),
                Div(
                    Label(
                        Span("From", cls="text-xs font-medium cc-muted"),
                        Input(
                            type="date",
                            name="date_from",
                            value=filters.date_from_display,
                            disabled=(filters.date_preset != "custom"),
                            data_dashboard_custom_date="true",
                            cls="input input-bordered input-sm w-full",
                        ),
                        cls="form-control",
                    ),
                    Label(
                        Span("To", cls="text-xs font-medium cc-muted"),
                        Input(
                            type="date",
                            name="date_to",
                            value=filters.date_to_display,
                            disabled=(filters.date_preset != "custom"),
                            data_dashboard_custom_date="true",
                            cls="input input-bordered input-sm w-full",
                        ),
                        cls="form-control",
                    ),
                    data_dashboard_date_fields="true",
                    cls=date_fields_cls,
                ),
                Label(
                    Span("Net worth chart", cls="text-xs font-medium cc-muted"),
                    Select(
                        *_select_options(data["net_worth_views"], filters.net_worth_view),
                        name="net_worth_view",
                        cls="select select-bordered select-sm w-full",
                    ),
                    cls="form-control",
                ),
                checklist_filter(
                    "Expense accounts",
                    "expense_account_id",
                    data["expense_accounts"],
                    expense_account_ids,
                    "dashboard-expense-account-select",
                    empty_summary="None",
                ),
                checklist_filter(
                    "Categories",
                    "category_id",
                    data["categories"],
                    category_ids,
                    "dashboard-category-select",
                    empty_summary="All",
                ),
                checklist_filter(
                    "Net worth accounts",
                    "net_worth_account_id",
                    data["net_worth_accounts"],
                    net_worth_account_ids,
                    "dashboard-net-worth-account-select",
                    empty_summary="None",
                ),
                cls="cc-dashboard-filter-body",
            ),
            Div(
                Input(type="hidden", name="expense_account_filter", value="1"),
                Input(type="hidden", name="net_worth_account_filter", value="1"),
                A("Reset", href="/dashboard", cls="btn btn-sm btn-ghost"),
                Button("Apply", type="submit", cls="btn btn-sm btn-primary"),
                cls="cc-dashboard-filter-actions",
            ),
            method="get",
            action="/dashboard",
            data_testid="dashboard-filters",
            cls="cc-dashboard-filter-panel cc-glass",
        ),
        Script(
            """
            (() => {
              const overlay = document.getElementById('dashboard-filter-overlay');
              if (!overlay) return;
              const preset = overlay.querySelector('[data-dashboard-date-preset]');
              const dateFields = overlay.querySelector('[data-dashboard-date-fields]');
              const dates = overlay.querySelectorAll('[data-dashboard-custom-date]');
              const syncDates = () => {
                const isCustom = preset?.value === 'custom';
                dateFields?.classList.toggle('hidden', !isCustom);
                dates.forEach((input) => { input.disabled = !isCustom; });
              };
              overlay.addEventListener('click', (event) => {
                if (event.target === overlay || event.target.classList.contains('cc-dashboard-filter-backdrop')) {
                  overlay.classList.remove('cc-open');
                }
              });
              preset?.addEventListener('change', syncDates);
              dates.forEach((input) => {
                input.addEventListener('input', () => {
                  if (preset && preset.value !== 'custom') {
                    preset.value = 'custom';
                    syncDates();
                  }
                });
              });
              syncDates();
            })();
            """
        ),
        id="dashboard-filter-overlay",
        cls="cc-dashboard-filter-overlay",
    )


def _select_options(options: list[tuple[str, str]], selected_value: str):
    return [
        Option(label, value=value, selected=(selected_value == value))
        for value, label in options
    ]


def _year_marker_overlay(markers: list[dict], testid: str, height_cls: str):
    if not markers:
        return ""

    return Div(
        *[
            Div(
                Div(
                    Span(marker["year"], cls="block text-[10px] font-medium text-base-content/70"),
                    Span(
                        marker.get("value", ""),
                        title=marker.get("value_label", ""),
                        data_year_marker_value=marker.get("value", ""),
                        cls="block text-[10px] font-medium text-base-content/60 whitespace-nowrap",
                    ) if marker.get("value") else "",
                    data_year_marker_label=marker.get("value_label", ""),
                    cls="absolute top-1 left-1 leading-tight",
                ),
                style=marker["left_style"],
                cls="absolute top-0 bottom-0 border-l border-base-content/35",
            )
            for marker in markers
        ],
        data_testid=testid,
        cls=f"absolute inset-0 {height_cls} pointer-events-none z-0",
    )


def _expense_trailing_average_overlay(data: dict):
    points = data.get("expense_trailing_avg_points") or ""
    if not points:
        return ""

    point_targets = []
    bars = data.get("expense_bars") or []
    for idx, point in enumerate(points.split()):
        try:
            x, y = point.split(",", 1)
        except ValueError:
            continue
        if idx >= len(bars):
            continue
        point_targets.append(
            Div(
                Span(cls="block h-1.5 w-1.5 rounded-full bg-warning/75 ring-1 ring-base-100/80"),
                Span(
                    f"{bars[idx]['month']}: {bars[idx]['trailing_avg_fmt']}",
                    cls="absolute bottom-full left-1/2 mb-2 -translate-x-1/2 rounded bg-base-300 px-2 py-1 text-xs text-base-content whitespace-nowrap opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-within:opacity-100",
                ),
                style=f"left:{x}%; top:{y}%",
                tabindex="0",
                aria_label=f"{bars[idx]['month']} 12-month average {bars[idx]['trailing_avg_fmt']}",
                data_trailing_avg_label=bars[idx]["trailing_avg_fmt"],
                cls="group absolute -translate-x-1/2 -translate-y-1/2 cursor-default pointer-events-auto focus:outline-none",
            )
        )

    return Div(
        Svg(
            ft(
                "polyline",
                points=points,
                fill="none",
                stroke="currentColor",
                stroke_width="2.5",
                vector_effect="non-scaling-stroke",
                data_series_kind="expense-trailing-average",
            ),
            viewBox="0 0 100 100",
            preserveAspectRatio="none",
            data_testid="expense-trailing-average-line",
            cls="absolute inset-0 h-36 w-full text-warning pointer-events-none",
        ),
        *point_targets,
        data_testid="expense-trailing-average-points",
        cls="absolute inset-0 h-36 w-full text-warning pointer-events-none z-20",
    )


def _net_worth_chart(data: dict):
    bars = data.get("nw_chart_bars") or []
    if not bars:
        return ""

    bar_divs = []
    for bar in bars:
        segments = []
        for segment in bar["segments"]:
            segments.append(
                Div(
                    style=f"{segment['height_style']}; background:{segment['color']}",
                    aria_label=f"{bar['month']} {segment['label']} {segment['value_fmt']}",
                    data_nw_segment_label=segment["label"],
                    data_nw_segment_value=segment["value_fmt"],
                    cls="relative w-full opacity-85 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100",
                )
            )
        bar_divs.append(
            Div(
                _stacked_bar_tooltip(
                    bar,
                    bar["total_fmt"],
                    "net-worth-month-tooltip",
                ),
                Span(
                    bar["total_compact"],
                    title=bar["total_fmt"],
                    style=bar["total_position_style"],
                    data_bar_total_label=bar["total_compact"],
                    cls="pointer-events-none absolute left-0 z-20 mb-1 w-full truncate text-center text-[9px] font-medium leading-none tabular-nums text-base-content/70",
                ),
                Div(*segments, cls="flex h-full w-full flex-col-reverse justify-start overflow-hidden rounded-t"),
                data_nw_total=bar["total_fmt"],
                data_cc_stacked_bar="true",
                tabindex="0",
                aria_label=f"{bar['month']} total net worth {bar['total_fmt']}",
                cls="group relative flex-1 flex flex-col items-end justify-end h-40 min-w-6 focus:outline-none",
            )
        )

    month_labels = [Div(bar["month"], cls="flex-1 truncate text-center text-xs cc-subtle") for bar in bars]
    legends = []
    for item in data.get("nw_chart_legend") or []:
        legends.append(
            Div(
                Span(cls="inline-block h-2 w-5 rounded", style=f"background:{item['color']}"),
                Span(item["label"], cls="text-xs cc-muted"),
                cls="flex items-center gap-1.5",
            )
        )

    return Div(
        Div(
            Div(
                Div(
                    _year_marker_overlay(data.get("nw_year_markers") or [], "net-worth-year-markers", "h-40"),
                    Div(*bar_divs, cls="relative z-10 flex items-end gap-1 h-40"),
                    _net_worth_trailing_average_overlay(data),
                    cls="relative",
                ),
                Div(*month_labels, cls="flex gap-1 mt-1"),
                style=data["nw_chart_width_style"],
                cls="cc-chart-canvas",
            ),
            data_testid="net-worth-chart-scroll",
            cls="cc-chart-scroll",
        ),
        Div(
            *legends,
            Div(
                Span(cls="inline-block h-0.5 w-6 rounded bg-warning"),
                Span("12-month avg", cls="text-xs cc-muted"),
                cls="flex items-center gap-1.5",
            ) if data.get("nw_trailing_avg_points") else "",
            cls="flex flex-wrap gap-4 mt-2",
        ),
        data_testid="net-worth-chart",
        cls="cc-chart-card cc-glass min-w-0 rounded-xl p-4",
    )


def _stacked_bar_tooltip(bar: dict, total: str, testid: str):
    rows = [
        Div(
            Span(segment["label"], title=segment["label"], cls="min-w-0 truncate cc-muted"),
            Span(segment["value_fmt"], cls="whitespace-nowrap text-right font-medium tabular-nums text-base-content"),
            data_stacked_bar_label=segment["label"],
            cls="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-5",
        )
        for segment in bar["segments"]
    ]
    return Div(
        Div(bar["month"], cls="mb-1 border-b border-base-300/70 pb-1 text-xs font-semibold text-base-content"),
        Div(
            Span("Total", cls="cc-muted"),
            Span(total, cls="whitespace-nowrap text-right font-semibold tabular-nums text-base-content"),
            data_stacked_bar_label="Total",
            cls="mb-1 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-5",
        ),
        *rows,
        aria_hidden="true",
        data_testid=testid,
        data_cc_stacked_tooltip="true",
        hidden=True,
        cls="cc-stacked-bar-tooltip rounded bg-base-300 px-3 py-2 text-xs text-base-content shadow-lg",
    )


def _stacked_bar_tooltip_behavior():
    return Script(
        """
        (() => {
          let floatingTooltip = null;

          const hideTooltip = () => {
            floatingTooltip?.remove();
            floatingTooltip = null;
          };

          const showTooltip = (bar) => {
            const source = bar.querySelector('[data-cc-stacked-tooltip]');
            if (!source) return;

            hideTooltip();
            floatingTooltip = source.cloneNode(true);
            floatingTooltip.hidden = false;
            floatingTooltip.removeAttribute('data-cc-stacked-tooltip');
            floatingTooltip.setAttribute('data-cc-floating-tooltip', 'true');
            Object.assign(floatingTooltip.style, {
              position: 'fixed',
              zIndex: '120',
              display: 'block',
              minWidth: '12rem',
              maxWidth: 'min(16rem, calc(100vw - 1rem))',
              maxHeight: 'calc(100vh - 1rem)',
              overflowY: 'auto',
              pointerEvents: 'none',
            });
            document.body.appendChild(floatingTooltip);

            const gap = 8;
            const edge = 8;
            const barRect = bar.getBoundingClientRect();
            const tooltipRect = floatingTooltip.getBoundingClientRect();
            const maxLeft = Math.max(edge, window.innerWidth - tooltipRect.width - edge);
            const left = Math.min(
              Math.max(barRect.left + barRect.width / 2 - tooltipRect.width / 2, edge),
              maxLeft,
            );

            let top = barRect.top - tooltipRect.height - gap;
            if (top < edge) top = barRect.bottom + gap;
            top = Math.min(
              Math.max(top, edge),
              Math.max(edge, window.innerHeight - tooltipRect.height - edge),
            );

            floatingTooltip.style.left = `${left}px`;
            floatingTooltip.style.top = `${top}px`;
          };

          document.querySelectorAll('[data-cc-stacked-bar]').forEach((bar) => {
            bar.addEventListener('mouseenter', () => showTooltip(bar));
            bar.addEventListener('mouseleave', hideTooltip);
            bar.addEventListener('focusin', () => showTooltip(bar));
            bar.addEventListener('focusout', () => {
              requestAnimationFrame(() => {
                if (!bar.contains(document.activeElement)) hideTooltip();
              });
            });
          });

          window.addEventListener('resize', hideTooltip);
          document.addEventListener('scroll', hideTooltip, true);
        })();
        """
    )


def _net_worth_trailing_average_overlay(data: dict):
    points = data.get("nw_trailing_avg_points") or ""
    if not points:
        return ""

    point_targets = []
    bars = data.get("nw_chart_bars") or []
    values = data.get("nw_trailing_avg_values") or []
    for idx, point in enumerate(points.split()):
        try:
            x, y = point.split(",", 1)
        except ValueError:
            continue
        if idx >= len(bars) or idx >= len(values):
            continue
        point_targets.append(
            Div(
                Span(cls="block h-1.5 w-1.5 rounded-full bg-warning/75 ring-1 ring-base-100/80"),
                Span(
                    f"{bars[idx]['month']}: {values[idx]}",
                    cls="absolute bottom-full left-1/2 mb-2 -translate-x-1/2 rounded bg-base-300 px-2 py-1 text-xs text-base-content whitespace-nowrap opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-within:opacity-100",
                ),
                style=f"left:{x}%; top:{y}%",
                tabindex="0",
                aria_label=f"{bars[idx]['month']} 12-month average net worth {values[idx]}",
                data_nw_trailing_avg_label=values[idx],
                cls="group absolute -translate-x-1/2 -translate-y-1/2 cursor-default pointer-events-auto focus:outline-none",
            )
        )

    return Div(
        Svg(
            ft(
                "polyline",
                points=points,
                fill="none",
                stroke="currentColor",
                stroke_width="2.5",
                vector_effect="non-scaling-stroke",
                data_series_kind="net-worth-trailing-average",
            ),
            viewBox="0 0 100 100",
            preserveAspectRatio="none",
            data_testid="net-worth-trailing-average-line",
            cls="absolute inset-0 h-40 w-full text-warning pointer-events-none",
        ),
        *point_targets,
        data_testid="net-worth-trailing-average-points",
        cls="absolute inset-0 h-40 w-full text-warning pointer-events-none z-20",
    )


def _net_worth_table(data: dict):
    if data.get("nw_table_rows"):
        header_cells = [Th("Account", cls="px-4 py-2 text-left font-medium cc-muted")]
        for month in data["nw_months"]:
            header_cells.append(Th(month, cls="px-3 py-2 text-right font-medium cc-muted"))

        body_rows = []
        for row in data["nw_table_rows"]:
            cells = [Td(row["label"], cls="px-4 py-2 text-base-content")]
            for balance in row["balances"]:
                cells.append(Td(balance, cls="px-3 py-2 text-right cc-muted"))
            body_rows.append(Tr(*cells, cls="border-b border-base-300/70 hover:bg-base-200/60"))

        return Div(
            Table(
                Thead(Tr(*header_cells, cls="border-b border-base-300")),
                Tbody(*body_rows),
                cls="table w-full text-sm",
            ),
            data_testid="net-worth-table",
            cls="cc-glass overflow-x-auto rounded-xl",
        )

    return P("No net worth data yet. Import account balances or add net worth transactions.", cls="text-sm cc-muted")
