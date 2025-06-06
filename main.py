from dotenv import load_dotenv
load_dotenv()

from gui import ChatbotGUI

def main() -> None:
    app = ChatbotGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
