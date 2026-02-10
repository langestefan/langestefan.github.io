---
layout: distill
title: Creating Interactive Blog Posts with WGLMakie.jl
date: 2025-02-13 19:35:00+0100
description: A tutorial on how to add interactive Makie.jl plots to your blog
tags: julia interactive makie.jl wglmakie.jl bonito.jl plots
categories: guides
related_posts: false
citation: true
giscus_comments: true
featured: true
toc:
  - name: A first example
  - name: A volume plot
  - name: Bonus - Plotting a Differential Equation
  - name: Conclusion
authors:
  - name: Stefan de Lange
    affiliations:
      name: TU Eindhoven
---

_Wouldn't it be cool to have 3D interactive visualizations right in your blog posts?_

Instead of just showing static images, you could let readers play around with interactive
plots—maybe to get a better handle on the data, or just for the fun of it. Since I
didn't want to depend on any backend services I am using static HTML files to host the
interactive plots. All code for this blog post
[is available on GitHub](https://github.com/langestefan/langestefan.github.io/tree/main/_posts/guides/interactive-blog).

I figured I couldn't be the first to think of this, and I wasn't wrong. I found
[Aaron's blog post](https://aarontrowbridge.github.io/posts/interactive-julia-plotting/),
which walks you through creating interactive plots on a web page using
[WGLMakie.jl](https://github.com/MakieOrg/Makie.jl/tree/master/WGLMakie)—the web-based
backend for the [Makie.jl](https://docs.makie.org/stable/) plotting library.

Aaron's method is now about four years old, and sadly it doesn't work anymore. I was
determined to make it happen, so I reached out for help and, as usual, the Julia
community came through.
[Simon Danisch](https://discourse.julialang.org/t/exporting-figures-to-static-html/125896/16?u=langestefan),
the creator of Makie.jl, shared some valuable tips on setting everything up and this blog
post is the result.

{% alert note %}
Besides WGLMakie.jl we will also need <a href="https://github.com/SimonDanisch/Bonito.jl">Bonito.jl</a>
to create the HTML descriptions, which will enable us to embed the plot in a blog post.
{% endalert %}

## A first example

First, we need a location to store the script that generates our plots. I prefer to
group all files for a specific post in a single folder. For this post, I created a
folder called `_posts/guides/interactive-blog/` and saved the script as `plots.jl`. As
a preliminary example we will just plot some random data.

{% include_code file="_posts/guides/interactive-blog/plots.jl" lang="julia" start="1" end="10" %}

And the code that generates the plot:

{% include_code file="_posts/guides/interactive-blog/plots.jl" lang="julia" start="13" end="27" %}

The script above creates a scatter plot with random data and saves it as `scatter.html`.
Which we can then include in our blog post using the following liquid:

```liquid
{% raw %}{% include_relative scatter.html %}{% endraw %}
```

{% alert warning %}
The HTML files created by `record_states` may be large, since it needs to record all
combinations of widget states. This could make your website less responsive. See the
<a href="https://simondanisch.github.io/Bonito.jl/stable/api.html#Bonito.record_states-Tuple%7BSession,%20Hyperscript.Node%7D">documentation</a> for more information.
{% endalert %}

This will render the scatter plot where the liquid tag is placed:

{% include_relative scatter.html %}

Cool right? Try moving the slider to change the size of the markers. You can also
click and drag to rotate the plot.

{% alert warning %}
We have to pay special attention to the `session` object. The first session will include
the setup for any session that’s included afterwards. You’ll also need to follow the
order of rendering, since new dependencies get included in the session that first “sees”
that dependency.
{% endalert %}

## A volume plot

To render multiple plots we need to use a `Subsession`, which skips uploading similar
assets/data and setup. The sub session can be created by calling `Session(session)` with
the parent session as an argument.

{% include_code file="_posts/guides/interactive-blog/plots.jl" lang="julia" start="30" end="36" %}

{% include_relative volume.html %}

## Bonus - Plotting a Differential Equation

Let's plot a differential equation using the [DifferentialEquations.jl](https://docs.sciml.ai/DiffEqDocs/stable/)
package. We will solve the Lorenz system of differential equations and plot the result.

{% include_code file="_posts/guides/interactive-blog/plots.jl" lang="julia" start="39" end="69" %}

{% include_relative diffeq.html %}

## Conclusion

We have seen how to create interactive plots using WGLMakie.jl and Bonito.jl. This is a
great way to engage your readers and make your blog posts more interactive. I hope you
found this tutorial useful and that you will start adding interactive plots to your blog!

{% alert note %}
This blog was tested with:

```yaml
Status `~/dev/projects/2026/langestefan.github.io/Project.toml`
[824d6782] Bonito v4.2.0
[5ae59095] Colors v0.13.1
[5789e2e9] FileIO v1.18.0
[1dea7af3] OrdinaryDiffEq v6.108.0
[276b4fcb] WGLMakie v0.13.8
```

{% endalert %}
