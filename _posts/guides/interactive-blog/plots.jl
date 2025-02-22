using Bonito, WGLMakie
using DifferentialEquations

output_file = "_posts/examples/diffeqviz/sinc_surface.html"

function as_html(io, session, app)
    dom = Bonito.session_dom(session, app)
    show(io, MIME"text/html"(), Bonito.Pretty(dom))
end

session = Session(NoConnection(); asset_server=NoServer())

# plot 1 - random scatter plot
open("_posts/guides/interactive-blog/scatter.html", "w") do io
    println(io, """<center>""")
    app = App() do 
        markersize = Bonito.Slider(range(0.01, stop=0.1, length=5))
        scale_value = DOM.div("\\(s = \\)", markersize.value)

        # Create a scatter plot
        fig, ax = meshscatter(rand(3, 100), markersize=markersize)
        
        # Return the plot and the slider
        return Bonito.record_states(session, DOM.div(fig, scale_value, markersize))
    end;
    as_html(io, session, app)
    println(io, """</center>""")
end

# open("_posts/examples/diffeqviz/contour.html", "w") do io
#     app = App() do 
#         markersize = Bonito.Slider(range(10, stop=100, length=100))

#         # Create a scatter plot
#         fig, ax = meshscatter(rand(3, 100), markersize=markersize)

#         # Return the plot and the slider
#         return Bonito.record_states(session, DOM.div(fig, markersize))
#     end;

#     as_html(io, session, app)
# end

# # plot 2 - volume plot
# open("_posts/examples/diffeqviz/sinc_surface.html", "w") do io
#     # create sub session
#     sub = Session(session)

#     app = App(volume(rand(10, 10, 10)))
#     as_html(io, sub, app)
# end

# open("_posts/examples/diffeqviz/diffeq.html", "w") do io
#     # Create a Bonito session
#     sub = Session(session)

#     # Define the Lorenz system
#     function lorenz!(du, u, p, t)
#         x, y, z = u
#         σ, ρ, β = p
#         du[1] = σ * (y - x)
#         du[2] = x * (ρ - z) - y
#         du[3] = x * y - β * z
#     end

#     # Time span and initial condition
#     tspan = (0.0, 40.0)
#     u0    = [1.0, 0.0, 0.0]

#     # Default parameters (classic Lorenz with adjustable β)
#     σ₀ = 10.0
#     ρ₀ = 28.0
#     β₀ = 2.666
#     p₀ = (σ₀, ρ₀, β₀)

#     # Create the initial ODE solution
#     prob = ODEProblem(lorenz!, u0, tspan, p₀)
#     sol  = solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8, saveat=0.05)

#     # Create a Makie figure with two rows:
#     # Row 1: 3D scene (LScene) with the Lorenz attractor.
#     # Row 2: A slider grid controlling the parameters.
#     fig = Figure(size = (900, 600))

#     # --- Row 1: 3D Plot ---
#     ax = LScene(fig[1, 1], show_axis=true)
#     lineplot = lines!(ax,
#         sol[1, :], sol[2, :], sol[3, :],
#         linewidth = 2
#     )

#     # --- Row 2: Slider Grid ---
#     sgrid = SliderGrid(fig[2, 1],
#         (label = "σ", range = LinRange(0, 20, 100)),
#         (label = "ρ", range = LinRange(0, 50, 100)),
#         (label = "β", range = LinRange(0, 10, 100))
#     )
#     σ_slider, ρ_slider, β_slider = sgrid.sliders

#     # Set the slider default values.
#     σ_slider.value[] = σ₀
#     ρ_slider.value[] = ρ₀
#     β_slider.value[] = β₀

#     # Function to re-solve the ODE and update the plot.
#     function update_plot!()
#         # Get the current parameter values from the sliders
#         σ = σ_slider.value[]
#         ρ = ρ_slider.value[]
#         β = β_slider.value[]
#         new_p = (σ, ρ, β)
#         new_prob = remake(prob, p = new_p)
#         new_sol  = solve(new_prob, Tsit5(), reltol=1e-8, abstol=1e-8, saveat=0.1)
#         # Update the line plot with the new solution
#         lineplot[1][] = Point3f0.(new_sol[1, :], new_sol[2, :], new_sol[3, :])
#     end

#     # Connect each slider’s observable to update_plot!
#     for slider in (σ_slider, ρ_slider, β_slider)
#         on(slider.value) do _
#             update_plot!()
#         end
#     end

#     # --- Bonito App ---
#     # Wrap the entire Makie figure (which includes the slider grid)
#     # in a recorded DOM container so that slider changes propagate.
#     app = App() do
#         # By calling `Bonito.record_states` on the container,
#         # all reactive states (including slider values) are captured.
#         Bonito.record_states(sub, DOM.div(fig))
#     end

#     # Write the Bonito app to an HTML file.
#     as_html(io, sub, app)
# end



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