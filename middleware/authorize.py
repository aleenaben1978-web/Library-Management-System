from flask import session, redirect, url_for

def admin_required():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Access denied. Admins only."

    return None