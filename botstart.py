import botlib
import getpass

name = raw_input("Username: ")
passw = getpass.getpass("Password: ")
low = raw_input("Low rank: ")
high = raw_input("High rank: ")
botlib.AlbumBot(name, passw, "s6.sfgame.gr").BeginAuto(int(low), int(high))