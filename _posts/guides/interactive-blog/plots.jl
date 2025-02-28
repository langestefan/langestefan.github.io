using Bonito, WGLMakie

output_folder = "_posts/guides/interactive-blog/"

function as_html(io, session, app)
    dom = Bonito.session_dom(session, app)
    show(io, MIME"text/html"(), Bonito.Pretty(dom))
end

session = Session(NoConnection(); asset_server=NoServer())

# plot 1 - random scatter plot
open(output_folder * "scatter.html", "w") do io
    println(io, """<center>""")
    app = App() do 
        markersize = Bonito.Slider(range(0.01, stop=0.11, length=6), value=0.07)
        scale_value = DOM.div("\\(s = \\)", markersize.value)

        # Create a scatter plot
        fig, ax = meshscatter(rand(3, 100), markersize=markersize, figure=(; size=(500, 500)))
        
        # Return the plot and the slider
        return Bonito.record_states(session, DOM.div(fig, scale_value, markersize))
    end;
    as_html(io, session, app)
    println(io, """</center>""")
end

# plot 2 - volume plot
open(output_folder * "volume.html", "w") do io
    println(io, """<center>""")
    sub = Session(session)
    app = App(volume(rand(10, 10, 10), figure=(; size=(500, 500))))
    as_html(io, sub, app)
    println(io, """</center>""")
end

# plot 3 - diffeq plot
using DifferentialEquations

function lorenz!(du, u, p, t)
    du[1] = 10.0 * (u[2] - u[1])
    du[2] = u[1] * (28.0 - u[3]) - u[2]
    du[3] = u[1] * u[2] - (8 / 3) * u[3]
end

u0 = [1.0; 0.0; 0.0]
tspan = (0.0, 100.0)

open(output_folder * "diffeq.html", "w") do io
    sub = Session(session)    
    println(io, """<center>""")

    app = App() do
        prob = ODEProblem(lorenz!, u0, tspan)
        sol = solve(prob)
        
        fig, ax, plt = lines(
            sol; idxs = (1, 2, 3), 
            axis = (; type = LScene),
            plotdensity = 10000, 
            color = 1:10000, 
            colormap = :plasma, 
            transparency = true
        )
    end
    as_html(io, sub, app)
    println(io, """</center>""")
end