using Bonito, WGLMakie
using DifferentialEquations

output_file = "_posts/examples/diffeqviz/sinc_surface.html"

function as_html(io, session, app)
    dom = Bonito.session_dom(session, app)
    show(io, MIME"text/html"(), Bonito.Pretty(dom))
end

session = Session(NoConnection(); asset_server=NoServer())

# plot 1 - interactive plot
open("_posts/examples/diffeqviz/contour.html", "w") do io
    app = App() do 
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
    # create sub session
    sub = Session(session)

    app = App(volume(rand(10, 10, 10)))
    as_html(io, sub, app)
end

# plot 3 - differential equation
open("_posts/examples/diffeqviz/diffeq.html", "w") do io
    # create sub session
    sub = Session(session)

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

    app = App() do

        # create the slider
        slider = Slider(1:6)

        # map slider values to surface states
        states = map(slider.value) do a_val
            p = [10.0, 28.0, a_val]
            prob = ODEProblem(lorenz, u_begin, tspan, p)
            sol = solve(prob, Tsit5(), reltol = 1e-8, abstol = 1e-8, saveat=0.1)

            x = [u[1] for u in sol.u]
            y = [u[2] for u in sol.u]
            z = [u[3] for u in sol.u]

            return (x=x, y=y, z=z)
        end   

        # Now “lift” each field out of the NamedTuple.
        x_obs = lift(s -> s.x, states)
        y_obs = lift(s -> s.y, states)
        z_obs = lift(s -> s.z, states)
        

        # create the figure
        fig, = plot(x_obs, y_obs, z_obs; 
            markersize=3.0, color=:blue
        ) 
    
        # Return the plot and the slider
        return Bonito.record_states(sub, DOM.div(fig, slider))
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