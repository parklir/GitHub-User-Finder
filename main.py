import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

DATA_FILE = "favorites.json"


def load_favorites():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_favorites():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=4)


def search_user():
    username = entry_search.get().strip()
    if not username:
        messagebox.showwarning("Ошибка", "Введите имя пользователя")
        return

    try:
        headers = {"User-Agent": "GitHub-User-Finder-App/1.0"}
        response = requests.get(f"https://api.github.com/users/{username}", headers=headers)

        if response.status_code == 200:
            user = response.json()
            display_user(user)
        elif response.status_code == 403:
            messagebox.showerror("Ошибка", "Превышен лимит запросов. Добавьте токен GitHub для увеличения лимита.")
        elif response.status_code == 404:
            messagebox.showerror("Ошибка", f"Пользователь '{username}' не найден")
        else:
            messagebox.showerror("Ошибка", f"Ошибка API: {response.status_code}")
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Ошибка", "Нет соединения с интернетом")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")


def display_user(user):
    clear_user_frame()

    user_data = {
        "Логин": user.get("login", "-"),
        "Имя": user.get("name", "-"),
        "ID": user.get("id", "-"),
        "Репозитории": user.get("public_repos", "-"),
        "Подписчики": user.get("followers", "-"),
        "Подписки": user.get("following", "-"),
        "Создан": user.get("created_at", "-")[:10] if user.get("created_at") else "-"
    }

    for i, (key, value) in enumerate(user_data.items()):
        tk.Label(user_frame, text=f"{key}:", font=("Arial", 10, "bold")).grid(row=i, column=0, sticky="w", padx=5,
                                                                              pady=2)
        tk.Label(user_frame, text=str(value), font=("Arial", 10)).grid(row=i, column=1, sticky="w", padx=5, pady=2)

    global current_user
    current_user = user

    if current_user["login"] in [fav["login"] for fav in favorites]:
        btn_favorite.config(text="Удалить из избранного", bg="red")
    else:
        btn_favorite.config(text="Добавить в избранное", bg="green")

    btn_favorite.grid(row=len(user_data), column=0, columnspan=2, pady=10)


def clear_user_frame():
    for widget in user_frame.winfo_children():
        widget.destroy()


def toggle_favorite():
    if not current_user:
        messagebox.showwarning("Ошибка", "Нет выбранного пользователя")
        return

    login = current_user["login"]
    if login in [fav["login"] for fav in favorites]:
        favorites[:] = [fav for fav in favorites if fav["login"] != login]
        save_favorites()
        messagebox.showinfo("Успех", f"Пользователь {login} удалён из избранного")
        btn_favorite.config(text="Добавить в избранное", bg="green")
    else:
        favorite = {
            "login": current_user["login"],
            "name": current_user.get("name", "-"),
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        favorites.append(favorite)
        save_favorites()
        messagebox.showinfo("Успех", f"Пользователь {login} добавлен в избранное")
        btn_favorite.config(text="Удалить из избранного", bg="red")

    update_favorites_list()


def update_favorites_list():
    for row in favorites_tree.get_children():
        favorites_tree.delete(row)
    for fav in favorites:
        favorites_tree.insert("", tk.END, values=(fav["login"], fav["name"], fav["added_at"]))


def load_favorite_user():
    selected = favorites_tree.selection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите пользователя из списка")
        return

    item = favorites_tree.item(selected[0])
    login = item["values"][0]

    entry_search.delete(0, tk.END)
    entry_search.insert(0, login)
    search_user()


def main():
    global window, entry_search, user_frame, btn_favorite, favorites_tree, current_user, favorites

    favorites = load_favorites()
    current_user = None

    window = tk.Tk()
    window.title("GitHub User Finder")
    window.geometry("800x600")

    # Поиск
    search_frame = tk.LabelFrame(window, text="Поиск пользователя", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(search_frame, text="Логин:").pack(side=tk.LEFT, padx=5)
    entry_search = tk.Entry(search_frame, width=30)
    entry_search.pack(side=tk.LEFT, padx=5)
    entry_search.bind("<Return>", lambda event: search_user())

    tk.Button(search_frame, text="Найти", command=search_user, bg="blue", fg="white").pack(side=tk.LEFT, padx=5)

    # Информация о пользователе
    user_frame = tk.LabelFrame(window, text="Информация о пользователе", padx=10, pady=10)
    user_frame.pack(fill="x", padx=10, pady=5)

    btn_favorite = tk.Button(user_frame, text="Добавить в избранное", command=toggle_favorite)

    # Избранное
    fav_frame = tk.LabelFrame(window, text="Избранные пользователи", padx=10, pady=10)
    fav_frame.pack(fill="both", expand=True, padx=10, pady=5)

    columns = ("login", "name", "added_at")
    favorites_tree = ttk.Treeview(fav_frame, columns=columns, show="headings")
    favorites_tree.heading("login", text="Логин")
    favorites_tree.heading("name", text="Имя")
    favorites_tree.heading("added_at", text="Дата добавления")
    favorites_tree.column("login", width=150)
    favorites_tree.column("name", width=200)
    favorites_tree.column("added_at", width=150)
    favorites_tree.pack(fill="both", expand=True)

    btn_frame = tk.Frame(fav_frame)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Загрузить выбранного", command=load_favorite_user, bg="green", fg="white").pack(
        side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Удалить из избранного", command=lambda: delete_favorite(), bg="red", fg="white").pack(
        side=tk.LEFT, padx=5)

    update_favorites_list()
    window.mainloop()


def delete_favorite():
    selected = favorites_tree.selection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите пользователя")
        return

    item = favorites_tree.item(selected[0])
    login = item["values"][0]

    if messagebox.askyesno("Подтверждение", f"Удалить {login} из избранного?"):
        favorites[:] = [fav for fav in favorites if fav["login"] != login]
        save_favorites()
        update_favorites_list()
        messagebox.showinfo("Успех", f"Пользователь {login} удалён")


if __name__ == "__main__":
    main()