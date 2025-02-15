# using WGLMakie, Bonito, FileIO
# WGLMakie.activate!()

# # mkpath("static/plot_html/interactive_plotting")
# output_file = "_posts/examples/diffeqviz/sinc_surface.html"


# open(output_file, "w") do io
#     println(io,
#         """
#         <center>
#         """
#     )
#     Page(exportable=true, offline=true)

#     app = App() do session::Session
#         # radial sinc function with scale parameter "a"
#         radial_sinc(x, y, a) = sinc(a * hypot(x, y)) 

#         # domain of surface
#         xs = LinRange(-5, 5, 150)
#         ys = LinRange(-5, 5, 150)

#         scale_slider = Slider(1:3)


#         states = map(scale_slider) do a
#             return [radial_sinc(x, y, a) for x in xs, y in ys]
#         end

#         fig, ax, = surface(xs, ys, states)

#         scale_value = DOM.div("\\(a = \\)", scale_slider.value)
        
#         return Bonito.record_states(
#             session,
#             DOM.div(fig, scale_value, scale_slider)
#         )
#     end

#     show(io, MIME"text/html"(), app)

#     println(
#         io,
#         """
#         </center>
#         """
#     )
# end

using Bonito, WGLMakie, Makie, Colors, FileIO
using Bonito.DOM

function styled_slider(slider, value)
    rows(slider, DOM.span(value, class="p-1"), class="w-64 p-2 items-center")
end

# Create a little interactive app
Page(exportable=true, offline=true)

app = App() do session
    markersize = Bonito.Slider(range(10, stop=100, length=100))

    # Create a scatter plot
    fig, ax = meshscatter(rand(3, 100), markersize=markersize)

    # Create a styled slider
    styled_slider(markersize, "Marker Size")

    # Return the plot and the slider
    return Bonito.record_states(session, DOM.div(fig, markersize))
end;

# mkdir("simple")
output_file = "_posts/examples/diffeqviz/sinc_surface.html"
Bonito.export_static(output_file, app)