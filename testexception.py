
"""
from turtle import color
from turtle import color


def choose_false(list_of_valid : list[str], question :str) :
    user_input = input(question)
    valid_int: bool = False

    while not valid_int:
        user_input = input(question) 
        if user_input in list_of_valid :
            return user_input
        else:
            return ValueError("Invalid choice. Please choose from: ")

color =     ["red", "green", "blue"]
try:
    picked = choose_false(color, "Pick a color: ")
except ValueError as e:
    print("An error occurred:", str(e))
else:
    print("You picked", picked)


def fastapi_engine(user_url):
    article_dir = get_api_function(user_url)
    try:
        response = api_function()
    except HTTPException as e:
        response = "ERROR 404"
    return response

   

valid_int: bool = False
user_input: str = ""
user_int: int = 0

while not valid_int:
    user_input = input("Entrez un nombre: ") 
    try:
        user_int = int(user_input) 
    except ValueError:
        print("Ce n'est pas un nombre valide. Veuillez réessayer.")
    else:
        valid_int = True

print("Vous avez entré", valid_int)"""

# Ask user to choose a filename in articles 
# And then pint its content. If the file does not exist, ask the user again 
# using try and except
from pathlib import Path

def show_article():
    ask_again = True
    content = ""
    while ask_again:
        fname = input("Enter article name: ").strip()
        file_path = Path(__file__).resolve().parent.parent / "articles" / (fname + ".md")
        try:
            content = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            print("Invalid filename")
        else:
            ask_again = False
    return content


if __name__ == "__main__":
    article_content = show_article()
    print(article_content)