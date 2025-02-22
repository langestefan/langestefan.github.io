---
layout: distill
title: Creating Interactive Blog Posts with WGLMakie.jl
date: 2025-02-13 19:35:00+0100
description: A tutorial on how to add interactive Makie.jl plots to your blog
tags: julia interactive makie.jl wglmakie.jl bonito.jl plots
categories: guides
related_posts: false
citation: true
---

*Wouldn't it be cool to have 3D interactive visualizations inside blog posts?*

From an engagement perspective this would be awesome. Instead of serving static
images, we could have interactive plots that the reader can play around with. Potentially
to better understand the data or topic at hand, but mostly because it's fun. Because 
we don't want to require any backend services, we need to use a client-side solution.
This means serving static HTML files that contain the interactive plots.

So naturally, I thought to myself "I can't be the first person to think of this". And 
ofcourse I wasn't. I found [this great blog post by Aaron](https://aarontrowbridge.github.io/posts/interactive-julia-plotting/)
which provides a step-by-step guide on how to create interactive plots on a web page using
[WGLMakie.jl](https://github.com/MakieOrg/Makie.jl/tree/master/WGLMakie), the web-based
backend for the [Makie.jl](https://docs.makie.org/stable/) plotting library. 

Aaron's blog post is now 4 years old and the method described there unfortunately no 
longer works. I was determined, but since I barely know what HTML is I needed a little help. 
I found out yet again how great, supportive and helpful the Julia community is. After 
posting on the [Julia Discourse](https://discourse.julialang.org/)
I got [a response from Simon Danisch](https://discourse.julialang.org/t/exporting-figures-to-static-html/125896/16?u=langestefan) who is the creator of Makie.jl. 



{% alert note %}
Besides WGLMakie.jl we will also need <a href="https://github.com/SimonDanisch/Bonito.jl">Bonito.jl</a>
to create the HTML descriptions, which will enable us to embed the plot in a blog post.
{% endalert %}

## A first example

This blog post, which can be read as a tutorial or recipe, is a direct translation from 
Simon's response into a working example. I hope it helps you to create interactive plots
for your blog posts.

First, we need a location to store the script that generates our plots. I prefer to 
group all files for a specific post in a single folder. For this post, I created a 
folder called `_posts/guides/interactive-blog/` and saved the script as `plots.jl`. As
a preliminary example we will just plot some random data.

```julia
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
```

{% alert warning %}
The HTML files created by `record_states` may be large, since it needs to record all 
combinations of widget states. This could make your website less responsive. See the
<a href="https://simondanisch.github.io/Bonito.jl/stable/api.html#Bonito.record_states-Tuple%7BSession,%20Hyperscript.Node%7D">documentation</a> for more information.
{% endalert %}

The script above creates a scatter plot with random data and saves it as `scatter.html`.
Which we can then include in our blog post using the following liquid:
```liquid
{% raw %}{% include_relative scatter.html %}{% endraw %}
```

This will render the scatter plot where the liquid tag is placed:

{% include_relative scatter.html %}

Cool right? Try moving the slider to change the size of the markers. You can also
click and drag to rotate the plot.

{% alert warning %}
We have to pay special attention to the `session` object. The first session will include 
the setup for any session that’s included afterwards. You’ll also need to follow  the 
order of rendering, since new dependencies get included in the session that first “sees” 
that dependency.
{% endalert %}
