import game


def main():
    game_instance = game.GameManager.get_instance()
    game_instance.run()


if __name__ == '__main__':
    main()
