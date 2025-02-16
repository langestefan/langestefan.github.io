using Bonito, WGLMakie
using DifferentialEquations

output_file = "_posts/examples/diffeqviz/sinc_surface.html"

function as_html(io, session, app)
    dom = Bonito.session_dom(session, app)
    show(io, MIME"text/html"(), Bonito.Pretty(dom))
end

session = Session(NoConnection(); asset_server=NoServer())
sub = Session(session)

# plot 1 - interactive plot
open("_posts/examples/diffeqviz/contour.html", "w") do io
    app = App() do session
        markersize = Bonito.Slider(range(10, stop=100, length=100))

        # Create a scatter plot
        fig, ax = meshscatter(rand(3, 100), markersize=markersize)

        # Return the plot and the slider
        return Bonito.record_states(session, DOM.div(fig, markersize))
    end;

    as_html(io, session, app)
end

# plot 2 - volume plot
open("_posts/examples/diffeqviz/sinc_surface.html", "w") do io
    app = App(volume(rand(10, 10, 10)))
    as_html(io, Session(session), app)
end

# plot 3 - differential equation
open("_posts/examples/diffeqviz/diffeq.html", "w") do io
    function lorenz(du, u, p, t)
        x, y, z = u
        sigma, rho, beta = p
        du[1] = sigma * (y - x)
        du[2] = x * (rho - z) - y
        du[3] = x * y - beta * z
    end

    t_begin = 0.0
    t_end = 100.0
    tspan = (t_begin, t_end)
    u_begin = [1.0, 0.0, 0.0]

    sub = Session(session)

    app = App() do
        a = Bonito.Slider(range(1, stop=100, length=100))

        # setup the ODE problem 
        sol = lift(a) do a_val
            p = [10.0, 28.0, a_val]
            prob = ODEProblem(lorenz, u_begin, tspan, p)
            solve(prob, Tsit5(), reltol = 1e-8, abstol = 1e-8)
        end

        x = [x[1] for x in sol[][:]]
        y = [x[2] for x in sol[][:]]
        z = [x[3] for x in sol[][:]]

        # lines!(ax, x, y, z) 
        # fig, = surface(x, y, z)
        fig, = meshscatter(x, y, z)

        # Return the plot and the slider
        return Bonito.record_states(sub, DOM.div(fig, a))
    end;

    as_html(io, sub, app)
end

# # plot 3 - differential equation
# open("_posts/examples/diffeqviz/diffeq.html", "w") do io

#     # function lorenz(du, u, p, t)
#     #     x, y, z = u
#     #     sigma, rho, beta = p
#     #     du[1] = sigma * (y - x)
#     #     du[2] = x * (rho - z) - y
#     #     du[3] = x * y - beta * z
#     # end

#     # t_begin = 0.0
#     # t_end = 10.0
#     # tspan = (t_begin, t_end)
#     # u_begin = [1.0, 0.0, 0.0]

#     app = App() do session

#         # create a slider
#         a = Bonito.Slider(range(1, stop=3, length=3))
    
#         # setup the ODE problem 
#         # sol = lift(a) do a_val
#         #     p = [10.0, 28.0, a_val]
#         #     prob = ODEProblem(lorenz, u_begin, tspan, p)
#         #     solve(prob, Tsit5(), reltol = 1e-8, abstol = 1e-8)
#         # end
    
#         # Create a 3D makie plot with the solution
#         # fig = Figure(size=(800, 400))
#         # ax = Axis3(fig[1, 1])
#         # x = Vector{Float64}(sol[][:][1, :])
#         # y = Vector{Float64}(sol[][:][2, :])
#         # z = Vector{Float64}(sol[][:][3, :])
    
#         # fig, ax = meshscatter(
#         #     x,
#         #     y,
#         #     z,
#         #     markersize=1
#         # )
    
#         # Create a scatter plot
#         fig, ax = meshscatter(rand(3, 100), markersize=markersize)

#         # Return the plot and the slider
#         return Bonito.record_states(session, DOM.div(fig, a))
#     end
# end