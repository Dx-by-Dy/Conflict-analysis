import highspy
from bnb import BnB

if __name__ == '__main__':
    B = BnB("test.lp")
    B.start()
    print(B.result())

    h = highspy.Highs()
    h.readModel("test.lp")
    h.silent()
    h.run()
    print(h.getSolution().col_value)

