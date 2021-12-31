from boldui import Ops, Expr, ProtocolServer

if __name__ == '__main__':
    initial_scene = [
        Ops.clear(0xff202030),

        # Left rectangle
        Ops.rect(
            (
                10,
                10,
                Expr.var('width') // 2 - 5,
                Expr.var('height') - 10,
            ),
            0xffa0a0a0
        ),

        # Right rectangle
        Ops.rect(
            (
                Expr.var('width') // 2 + 5,
                10,
                Expr.var('width') - 10,
                Expr.var('height') - 10,
            ),
            0xffa0a0a0
        ),

        # Rect in the middle (border)
        Ops.rect(
            (
                (Expr.var('width') // 2) - 60,
                (Expr.var('height') // 2) - 60,
                (Expr.var('width') // 2) + 60,
                (Expr.var('height') // 2) + 60,
            ),
            0xff202030,
        ),

        # Rect in the middle
        Ops.rect(
            (
                (Expr.var('width') // 2) - 50,
                (Expr.var('height') // 2) - 50,
                (Expr.var('width') // 2) + 50,
                (Expr.var('height') // 2) + 50,
            ),
            0xffc08080,
        ),
    ]

    server = ProtocolServer("/tmp/boldui.hello_world.sock", initial_scene)
    server.serve()
