from fasthtml.common import *


THEMES = [
    ("abyss", "Abyss"),
    ("night", "Night"),
    ("business", "Business"),
    ("nord", "Nord"),
    ("emerald", "Emerald"),
    ("cupcake", "Cupcake"),
]


def theme_select(select_id: str, extra_cls: str = "", width_cls: str = "w-36"):
    options = [Option(label, value=value) for value, label in THEMES]
    cls = f"select select-sm {width_cls}"
    if extra_cls:
        cls = f"{cls} {extra_cls}"
    return Select(
        *options,
        id=select_id,
        cls=cls,
        onchange="""
        document.documentElement.setAttribute('data-theme', this.value);
        localStorage.setItem('cashcompass-theme', this.value);
        document.querySelectorAll('[data-theme-picker]').forEach((el) => { el.value = this.value; });
        """,
        data_theme_picker="true",
    )


def nav_bar(active: str):
    def link(href, name, label):
        cls = "text-primary font-semibold" if active == name else "text-base-content/70 hover:text-base-content"
        return A(label, href=href, cls=cls)

    def mobile_link(href, name, label):
        cls = "text-primary font-semibold" if active == name else "text-base-content/70"
        return A(label, href=href, cls=cls)

    return Nav(
        Div(
            A("Cash Compass", href="/", cls="text-sm font-semibold text-base-content tracking-wide"),
            Div(
                link("/dashboard", "dashboard", "Dashboard"),
                link("/accounts", "accounts", "Accounts"),
                link("/categories", "categories", "Categories"),
                link("/transactions", "transactions", "Transactions"),
                link("/settings", "settings", "Settings"),
                cls="hidden md:flex items-center gap-6 text-sm",
            ),
            Div(
                Label("Theme", fr="theme-picker", cls="sr-only"),
                theme_select("theme-picker"),
                cls="hidden md:flex items-center gap-2",
            ),
            Button(
                "☰",
                cls="btn btn-ghost btn-sm md:hidden text-xl",
                onclick="document.getElementById('mobile-nav').classList.toggle('hidden')",
            ),
            cls="mx-auto flex max-w-5xl items-center justify-between px-6 h-16 gap-4",
        ),
        Div(
            mobile_link("/dashboard", "dashboard", "Dashboard"),
            mobile_link("/accounts", "accounts", "Accounts"),
            mobile_link("/categories", "categories", "Categories"),
            mobile_link("/transactions", "transactions", "Transactions"),
            mobile_link("/settings", "settings", "Settings"),
            theme_select("theme-picker-mobile", "mt-2"),
            id="mobile-nav",
            cls="hidden md:hidden cc-glass border-t border-base-300/60 px-6 py-4 flex flex-col gap-3 text-sm",
        ),
        Script(
            """
            (() => {
              const syncThemePickers = () => {
                const theme = document.documentElement.getAttribute('data-theme') || localStorage.getItem('cashcompass-theme') || 'abyss';
                document.querySelectorAll('[data-theme-picker]').forEach((el) => { el.value = theme; });
              };
              syncThemePickers();
              document.addEventListener('DOMContentLoaded', syncThemePickers);
            })();
            """
        ),
        cls="fixed top-0 left-0 right-0 z-50 border-b border-base-300/60 bg-base-100/85 backdrop-blur",
    )


def page_layout(active_nav: str, *content):
    return (
        nav_bar(active_nav),
        Main(
            *content,
            cls="mx-auto flex w-full max-w-5xl flex-col gap-10 px-6 pt-24 pb-12",
        ),
    )


def crud_page_layout(header, form_content, list_content):
    return (
        header,
        Div(
            Section(
                form_content,
                cls="cc-crud-sidebar",
            ),
            Section(
                list_content,
                cls="cc-crud-main",
            ),
            cls="cc-crud-layout",
        ),
    )
