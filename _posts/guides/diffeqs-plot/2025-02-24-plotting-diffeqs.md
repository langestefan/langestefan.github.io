---
layout: distill
title: Plotting Differential Equations with WGLMakie.jl
date: 2025-02-24 15:09:00
description: an example of a blog post with some code
tags: formatting code
categories: guides
citation: true
giscus_comments: true
---

In this blog post we will walk through the process of visualizing [DifferentialEquations.jl](https://docs.sciml.ai/DiffEqDocs/stable/) solutions using [WGLMakie.jl](https://github.com/MakieOrg/Makie.jl/tree/master/WGLMakie).

## Demo: Soccer ball trajectory

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
- Given some initial velocity $\vec{v}_0$, what is the angle of the kick that maximizes 
  the horizontal distance the ball will travel?
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

Where $C_L$ is the lift coefficient and $f(\theta)$ is a
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
angular velocity of the ball. We will assume that $C_L$ takes the following simplified 
form:

$$
\begin{align}
    C_L &= \frac{\omega r}{\left| \vec{v} \right|}\\
    \omega &= \omega_0 \cdot \exp\left(-\frac{t}{7}\right)
\end{align}
$$

Where $\omega_0$ is the initial angular velocity just after the kick. We will solve this 
system numerically to obtain the trajectory of the ball after kicking it.
</div>

For those playing along at home, a table with all problem constants is given below:

| Symbol | Description | Value |
|--------|-------------|-------|
| $m$ | mass of the ball | 0.43 kg |
| $g$ | acceleration due to gravity | 9.81 m/s$^2$ |
| $\rho$ | air density | 1.225 kg/m$^3$ |
| $A$ | cross-sectional area of the ball | 0.013 m$^2$ |
| $C_D$ | drag coefficient | 0.2 |
| $r$ | radius of the ball | 0.11 m |
| $\omega_0$ | initial angular velocity | 88 rad/s |


Now we can finally start writing code! Which should be a breeze because we have 
access to [DifferentialEquations.jl](https://docs.sciml.ai/DiffEqDocs/stable/),
a package that provides a high-level interface for solving differential equations. 