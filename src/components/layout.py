from fasthtml.common import *


def nav_bar(active: str):
    def link(href, name, label):
        cls = "text-emerald-400 font-semibold" if active == name else "text-slate-400 hover:text-slate-100"
        return A(label, href=href, cls=cls)

    def mobile_link(href, name, label):
        cls = "text-emerald-400 font-semibold" if active == name else "text-slate-400"
        return A(label, href=href, cls=cls)

    return Nav(
        Div(
            A("Cash Compass", href="/", cls="text-sm font-semibold text-white tracking-wide"),
            Div(
                link("/dashboard", "dashboard", "Dashboard"),
                link("/accounts", "accounts", "Accounts"),
                link("/categories", "categories", "Categories"),
                link("/transactions", "transactions", "Transactions"),
                link("/settings", "settings", "Settings"),
                cls="hidden md:flex items-center gap-6 text-sm",
            ),
            Button(
                "☰",
                cls="md:hidden text-slate-400 text-xl",
                onclick="document.getElementById('mobile-nav').classList.toggle('hidden')",
            ),
            cls="mx-auto flex max-w-5xl items-center justify-between px-6 h-14",
        ),
        Div(
            mobile_link("/dashboard", "dashboard", "Dashboard"),
            mobile_link("/accounts", "accounts", "Accounts"),
            mobile_link("/categories", "categories", "Categories"),
            mobile_link("/transactions", "transactions", "Transactions"),
            mobile_link("/settings", "settings", "Settings"),
            id="mobile-nav",
            cls="hidden md:hidden bg-slate-900 border-t border-slate-800 px-6 py-3 flex flex-col gap-3 text-sm",
        ),
        cls="fixed top-0 left-0 right-0 z-50 bg-slate-900 border-b border-slate-800",
    )


def page_layout(active_nav: str, *content):
    return (
        nav_bar(active_nav),
        Main(
            *content,
            cls="mx-auto flex w-full max-w-5xl flex-col gap-10 px-6 pt-20 pb-12",
        ),
    )
