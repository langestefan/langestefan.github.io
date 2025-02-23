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
the setup for any session that’s included afterwards. You’ll also need to follow  the 
order of rendering, since new dependencies get included in the session that first “sees” 
that dependency.
{% endalert %}

## A second example

To render multiple plots we need to use a `Subsession`, which skips uploading similar 
assets/data and setup. The sub session can be created by calling `Session(session)` with
the parent session as an argument.

{% include_code file="_posts/guides/interactive-blog/plots.jl" lang="julia" start="30" end="34" %}

{% include_relative volume.html %}

## (Bonus) A DifferentialEquations.jl example

Now for a more exciting example, we will use the 
[DifferentialEquations.jl](https://docs.sciml.ai/DiffEqDocs/stable/) package to calculate
the position of a soccer ball after giving it a kick and use [Makie.jl](https://docs.makie.org/stable/) 
to visualize the resulting trajectory.

We will start from a physical description of the problem. This description is derived
from Newton's second law of motion, which states that the acceleration of an object is
directly proportional to the net forces acting on it. An excellent summary of the 
physics involved can be found in a series of blog posts by Hugo, namely [Bend it like Newton: curves in football](http://chalkdustmagazine.com/blog/bend-it-like-newton-curves-in-football/), [The maths behind a chip goal](https://chalkdustmagazine.com/blog/the-maths-behind-a-chip-goal/) and [Football free-kicks… taken by Newton](https://chalkdustmagazine.com/blog/free-kicks/).

<div style="margin-top: 20px; margin-bottom: -100px;"><center>
<svg viewBox="0 0 250 250">
  {% include_relative soccerball.svg %}
</svg></center></div>

<div class="theorem-box" markdown="1">
### The trajectory of a soccer ball

The position of a soccer ball in three dimensions can be described by a vector 
$\vec{x} = [x, y, z]^T$, its velocity by $\vec{v} = [v_x, v_y, v_z]^T $. The
initial position of the ball is $\vec{p}_0$, and the initial velocity is $\vec{v}_0$.

Newton's second law of motion relates the acceleration of the ball to the forces acting
on it. Mathematically, this can be written as:

$$
\begin{equation}
    m \cdot \vec{a} = m \frac{d^2}{dt^2}\vec{x} = \vec{F_G} + \vec{F_D} + \vec{F_L}
\end{equation}
$$

Where we consider the gravitational force $\vec{F_G}$, the drag force $\vec{F_D}$ and the
lift force $\vec{F_L}$. We are interested in solving this equation for $\vec{x}$ because
that will give us the position of the ball (with mass $m$) at any given time $t$.

We will refer to the <i>trajectory</i> of the ball as the time-dependent position vector 
$\vec{x}(t)$.
</div>

There are a bunch of interesting questions we can ask in this general problem context.
A few that come to mind are:
- How does the trajectory of the ball change when we change the initial velocity $\vec{v}_0$?
- Given some initial velocity $\vec{v}_0$, what is the maximum horizontal distance the ball can travel?
- Given (noisy) observations of a ball's trajectory, can we estimate what the initial 
  position $\vec{p}_0$ and velocity $\vec{v}_0$ were? Or even more interesting, can we
  predict where the ball will land while it is still in the air?

<div class="theorem-box" markdown="1">
### Forces affecting a ball’s trajectory

The gravitational force $\vec{F_G}$ is given by:

$$
\begin{equation}
    \vec{F_G} = -m \vec{g}
\end{equation}
$$

Where $\vec{g} = [0, 0, 9.81]^T$ is the downward acceleration due to gravity. The drag 
force $\vec{F_D}$ is the aerodynamic force that opposes the motion of the ball due to air
resistance. It is given by:

$$
\begin{equation}
    \vec{F_D} = -\frac{1}{2} \rho A C_D \left| \vec{v} \right| \cdot \vec{v} 
\end{equation}
$$

Where $\rho$ is the air density, $A$ is the cross-sectional area of the ball,
$C_D$ is the drag coefficient, $v$ is the velocity of the ball and 
$\left| \vec{v} \right| = \sqrt{v_x^2 + v_y^2 + v_z^2}$ is the magnitude of the velocity.

The lift force $\vec{F_L}$, or Magnus force, is the force that causes the ball to curve
in flight and is perpendicular to the velocity vector of the ball $\vec{v}$. It is given 
by:

$$
\begin{equation}
    \vec{F_L} = \frac{1}{2} \rho A C_L \left| \vec{v} \right| \cdot \vec{v} \cdot f(\theta)
\end{equation}
$$

Where $C_L$ is the lift coefficient, $\theta$ is the angle of attack and $f(\theta)$ is a
function that depends on the spin angle of the ball. Let's assume that the ball is spinning
around the $z$-axis, then $f(\theta) = [-1, 1, 0]^T$ where we assume that the dependence
on the angular velocity $\omega$ is already included in $C_L$.
</div>

We are now almost there. We have a physical description of the problem, but this 
description is only solvable analytically in specific, simplified cases. We need to
write out the equations in a form that can be solved numerically, so that we can then
use the `DifferentialEquations.jl` package to integrate the equations of motion which
will give us the trajectory of the ball.

<div class="theorem-box" markdown="1">
### System of differential equations

To make it easier to write out the equations of motion, we will introduce the
constant $H = \frac{\rho A}{2m}$, which will simplify the equations. 

Using the fact that $\frac{dx}{dt} = v_x, \frac{dy}{dt} = v_y, \frac{dz}{dt} = v_z$ the 
system of differential equations can then be written as:

<!-- $$
\begin{align}
    H &= \frac{\rho A}{2m} \\
    \left| \vec{v} \right| &= \sqrt{v_x^2 + v_y^2 + v_z^2}
    % C_L &= \left| \vec{v} \right|^{-1} \omega r \\ % C_L &= \frac{\omega r}{\left| \vec{v} \right|}\\
    % \omega &= \omega_0 \cdot \exp\left(-\frac{t}{\tau}\right)    
\end{align}
$$ -->

$$
\begin{align}
    \vec{a} &= -\left | \vec{v}\right | H      
    \begin{bmatrix}
      C_D \cdot v_x + C_L \cdot v_y \\
      C_D \cdot v_y - C_L \cdot v_x \\
      C_D \cdot v_z - g
    \end{bmatrix}
\end{align}
$$

The value of $C_L$ is usually derived from experiments and depends on the speed and 
angular velocity of the ball. We will assume that $C_L$ takes the following form:

$$
\begin{align}
    C_L &= \frac{\omega r}{\left| \vec{v} \right|}\\
    \omega &= \omega_0 \cdot \exp\left(-\frac{t}{\tau}\right)
\end{align}
$$

Where $\omega_0$ is the initial angular velocity and $\tau$ is the time constant. We 
will solve this system numerically to get the trajectory of the ball. 
</div>

Now we can finally start writing code! Which should be a breeze after because we have 
access to [DifferentialEquations.jl](https://docs.sciml.ai/DiffEqDocs/stable/).

{% include_code file="_posts/guides/interactive-blog/plots.jl" lang="julia" start="30" end="50" %}