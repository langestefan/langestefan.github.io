using WGLMakie, Bonito, FileIO
WGLMakie.activate!()

# mkpath("static/plot_html/interactive_plotting")
output_file = "_posts/examples/diffeqviz/sinc_surface.html"

open(output_file, "w") do io
    println(
        io,
        """
<center>
"""
    )
    Page(exportable=true, offline=true)

    app = App() do
        n = 7
        volume = rand(n, n, n)
        fig, _, _ = contour(volume, figure=(size=(700, 700),))
        fig
    end
    show(io, MIME"text/html"(), app)

    println(
        io,
        """
</center>
"""
    )
end