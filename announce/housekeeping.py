from announce import models


def handle(args):
    """
    Define multiple fuctions here.
    All functions must take 0 arguments.

    Then you can call them using `python -m announce run --fn <fn name>`
    """

    def hello():
        print("hello")

    def new_otp():
        tg_handle = input("TG handle: ")
        session = models.Session()
        try:
            otp = models.Otp.loop_create(session, tg_handle=tg_handle)
            print(otp.otp)
        finally:
            session.close()

    exec(f"{args.fn}()", globals(), locals())
