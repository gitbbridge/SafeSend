# SafeSend Design System

SafeSend's visual language lives in `app/design_system`. New screens should consume this package instead of defining local colors, fonts, spacing, button styles, card styles, table styles, or icon strings. Customer-facing shell, shared fields, shared tables, help surfaces, and navigation are backed by CustomTkinter.

## Themes

`app/design_system/theme.py` defines `NEW_SKIN` and `ORIGINAL_SKIN`. The active theme is selected with `SAFESEND_SKIN`; unset or `new` uses the New Skin, while `original` uses the Original Skin values.

`apply_theme(root)` applies the remaining ttk compatibility styles from the design-system modules. `app/design_system/components.py` is the canonical CustomTkinter component catalog. `app/design_system/customtkinter_adapter.py` remains as a compatibility facade so older screens can migrate without changing every import at once. Existing screens can keep importing from `app.ui.theme`; that module is also a compatibility facade over `app.design_system`.

## Component Catalog

Use these components before creating page-local widgets. The canonical implementation lives in `app/design_system/components.py`.

- `button()` with `primary`, `secondary`, `danger`, and `ghost` variants.
- `text_input()` with `default`, `focus`, `error`, and `disabled` visual states.
- `dropdown()`
- `checkbox()`
- `toggle()`
- `Card`
- `MetricCard`
- `SidebarItem`
- `PageHeader`
- `Toolbar`
- `table()`
- `Modal`
- `attach_tooltip_to()`
- `AIAssistantPanel`
- `EmptyState`
- Layout builders: `app_shell()`, `sidebar()`, `sidebar_section()`, `top_navigation()`, `page_container()`, `content_area()`, `section()`, `panel()`, `split_panel()`, `drawer()`, `inspector_panel()`, `Accordion`, `Stack`, `Grid`, `scrollable_container()`.
- Navigation builders: `navigation_menu()`, `breadcrumbs()`, `tabs()`, `segmented_control()`, `pagination()`, `wizard()`, `step_indicator()`, `previous_next()`, `context_menu()`, `overflow_menu()`, and `dropdown_menu()`.
- Button builders: `primary_button()`, `secondary_button()`, `ghost_button()`, `danger_button()`, `success_button()`, `icon_button()`, `split_button()`, `loading_button()`, `dropdown_button()`, `button_group()`, and `floating_action_button()`.
- Input builders: `password_input()`, `email_input()`, `number_input()`, `phone_input()`, `search_box()`, `search_with_filters()`, `text_area()`, `rich_text_editor()`, and `code_editor()`.
- Selection builders: `checkbox_group()`, `radio_button()`, `radio_group()`, `toggle_group()`, `select_dropdown()`, `multi_select()`, `tag_selector()`, `color_picker()`, `date_picker()`, `time_picker()`, `date_range_picker()`, `slider()`, and `stepper()`.
- Data/status builders: `modern_table()`, `data_grid()`, `tree_view()`, `property_grid()`, `statistics_card()`, `metric_card()`, `info_card()`, `list_view()`, `timeline()`, `activity_feed()`, `log_viewer()`, `json_viewer()`, `status_badge()`, `tag()`, `pill()`, `alert()`, `toast_notification()`, `banner()`, `progress_bar()`, `circular_progress()`, `loading_spinner()`, `skeleton_loader()`, `status_dot()`, `connection_indicator()`, and `health_indicator()`.
- Dialog builders: `confirmation_dialog()`, `Modal`, `wizard_dialog()`, `warning_dialog()`, `success_dialog()`, `delete_confirmation()`, `input_dialog()`, `progress_dialog()`, and `about_dialog()`.
- Help builders: `popover()`, `help_bubble()`, `inline_help()`, `guided_configuration_card()`, `ai_recommendation_card()`, `documentation_link()`, and `did_you_know_card()`.
- Chart builders: `line_chart()`, `area_chart()`, `bar_chart()`, `horizontal_bar_chart()`, `pie_chart()`, `donut_chart()`, `gauge()`, `progress_ring()`, `funnel()`, `heat_map()`, `scatter_plot()`, `timeline_chart()`, `sparkline()`, `world_map()`, `us_map()`, and `calendar_heatmap()`.
- SafeSend domain builders: email preview, campaign, SMTP, deliverability, contact, AI, file, settings, security, notification, and SafeSend-specific score/health/risk/analytics components.
- Page templates: dashboard, data management, settings, wizard, analytics dashboard, campaign builder, compose email, SMTP manager, contacts, reports, AI assistant, deliverability center, verification center, license management, and help center templates.

All new customer-facing UI should import from `app.design_system.components` or from shared wrappers that consume it. Do not create a new local button/card/input style in an individual screen.

## Colors

All color tokens are in `app/design_system/colors.py` as `Palette`. Use semantic tokens such as `theme.palette.background`, `theme.palette.surface`, `theme.palette.border`, `theme.palette.button_background`, `theme.palette.table_selected`, and `theme.palette.success`.

Do not place hex colors in UI screens. Add a semantic token to `Palette` if a future feature needs a new visual role.

## Typography

All font roles are in `app/design_system/typography.py`. Use roles like `page_title`, `section_header`, `card_header`, `body`, `caption`, `button`, `table`, `status_badge`, `tooltip`, `editor`, and `source`.

Use `font(theme, role)` for direct Tk widgets that cannot consume ttk styles.

## Spacing And Layout

Spacing tokens live in `app/design_system/spacing.py`; fixed layout dimensions live in `app/design_system/layout.py`. Use `theme.spacing.page_padding`, `card_padding`, `toolbar_padding`, `grid_gap`, `button_pad_x`, `button_pad_y`, `table_row_height`, and `sidebar_width` instead of magic numbers.

## Buttons

Button style definitions live in `app/design_system/buttons.py`.

Prefer CustomTkinter buttons from `app.design_system.components.button()` for new UI. Use the remaining ttk styles only for legacy code:
- `TButton` for standard secondary buttons.
- `Primary.TButton` only for true primary actions.
- `Toolbar.TButton`, `Icon.TButton`, `Danger.TButton`, and `Success.TButton` for specialized commands.
- `icon_text("save", "Save")` from `app.design_system.icons` for consistent icon prefixes.

Button variants:

- `primary`: the main save/create/run action on a surface.
- `secondary`: normal commands.
- `danger`: destructive actions such as delete/remove.
- `ghost`: low-emphasis sidebar, inline, or optional commands.

## Cards

Card styles live in `app/design_system/cards.py`. Use `Card.TFrame` for normal cards, or specialized styles such as `StatisticsCard.TFrame`, `ChartCard.TFrame`, `HelpCard.TFrame`, and `WarningCard.TFrame`.

Future cards should use `Card` or `MetricCard` from `app.design_system.components`, `theme.spacing.card_padding`, and the shared label roles.

## Tables

Table style configuration lives in `app/design_system/tables.py`. Existing `app.ui.shared.build_tree()` now returns the CustomTkinter-backed `ModernTable`, with alternating rows, custom headers, softer selection, and modern empty states.

Use `table()` or `app.ui.shared.build_tree()` for tables. Use `insert_table_row()`, `insert_empty_row()`, and `fill_tree()` from `app.ui.shared` when adding rows so the table keeps consistent row color, spacing, and empty-state behavior.

## Forms

Form control styles live in `app/design_system/forms.py`. New forms should use `text_input()`, `dropdown()`, `checkbox()`, and `toggle()` from `app.design_system.components`, or the shared form helpers in `app.ui.shared`. Validation and helper text should use the `error` input state and muted/danger label styling.

## Status Badges

Status badge mapping lives in `app/design_system/status_badges.py`. Use `status_style(level)` or `create_status_badge()` to keep statuses consistent. Supported semantic levels include `healthy`, `connected`, `disconnected`, `paused`, `running`, `queued`, `completed`, `failed`, `warning`, `suppressed`, `verified`, and `unknown`.

## Icons And Assets

Icon text mappings live in `app/design_system/icons.py`. Logo and application icon paths live in `app/design_system/assets.py`.

Do not hardcode icon strings or asset paths in screens. Add new entries to the registry when a new route or command is introduced.

## Charts

Chart defaults live in `app/design_system/charts.py`. Use `chart_colors(theme)` and `CHART_SPEC` for new charts so margins, grid styling, and color choices stay consistent.

## Tooltips

Tooltip behavior and styling live in `app/design_system/tooltips.py`. Use `attach_tooltip_to(widget, text)` or `tooltip(widget, help_text(...))` instead of hand-built tooltip windows.

## Component Builders

`app/design_system/helpers.py` provides reusable builders:
- `create_page_header()`
- `create_toolbar()`
- `create_statistics_card()`
- `create_help_panel()`
- `create_section_header()`
- `create_primary_button()`
- `create_table()`
- `create_status_badge()`
- `create_chart_card()`

New screens should be assembled from these helpers first. If a screen needs a repeated visual pattern, add a helper to the design system before copying layout code.

## Consistency Rules

Keep business logic, service calls, and database access out of design-system modules.

Avoid duplicate visual constants in `app/ui`. If a screen needs a visual value, it should come from `active_theme()`, a design-system module, or a shared UI helper.

Dark mode is not implemented yet, but the design system is theme-ready: adding it should mean adding another `SafeSendTheme` value and selecting it in `active_theme()`.
