import crear_input
import solver
import paint_a_solution
i = 0
while i < 100:
    crear_input.main()
    solver.resuelve_rutas()
    paint_a_solution.paint()
    i += 1