import reflex as rx

def index() -> rx.Component:
    return rx.center(
        rx.text("Hello Reflex"),
        height="100vh",
        align_items="center",
    )

app = rx.App()
app.add_page(index, route="/")

