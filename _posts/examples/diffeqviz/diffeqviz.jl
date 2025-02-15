using Bonito, WGLMakie


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
    as_html(io, sub, app)
end