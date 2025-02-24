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
    sub = Session(session)
    app = App(volume(rand(10, 10, 10), figure=(; size=(500, 500))))
    as_html(io, sub, app)
end

# plot 3 - differential equation

struct C
    m::Float64 # mass of the ball
    g::Float64 # acceleration due to gravity
    ρ::Float64 # density of the air
    A::Float64 # cross-sectional area of the ball
    C_D::Float64 # drag coefficient
    r::Float64 # radius of the ball
    ω₀::Float64 # initial angular velocity
end

struct IC
    x::Float64 # initial x position
    y::Float64 # initial y position
    z::Float64 # initial z position
    v_x::Float64 # initial x velocity
    v_y::Float64 # initial y velocity
    v_z::Float64 # initial z velocity
end


using DifferentialEquations

C₁ = C(0.43, 9.81, 1.225, 0.013, 0.2, 0.11, 88)
IC₁ = IC(0, 0, 0, 20, 0, 0)

# Define the ODE function. The state vector u = [x, y, z, vx, vy, vz]
function projectile!(ddu, du, u, p, t)
    # Unpack state variables
    x, y, z = u
    vx, vy, vz = du

    # Unpack parameters
    m, g, ρ, A, C_D, r, ω₀ = p

    # Define constant H = (ρ * A) / (2 * m)
    H = (ρ * A) / (2 * m)

    # Compute speed (magnitude of velocity)
    v = sqrt(vx^2 + vy^2 + vz^2)

    # Compute the decaying angular velocity ω(t)
    ω = ω₀ * exp(-t/7)

    # Compute lift coefficient, avoiding division by zero.
    C_L = (v == 0.0 ? 0.0 : (ω * r / v))

    # Compute acceleration components
    ddu[1] = -v * H * (C_D * vx + C_L * vy)
    ddu[2] = -v * H * (C_D * vy - C_L * vx)
    ddu[3] = -v * H * (C_D * vz - g)
end

# Problem constants:
# m: mass (kg), g: gravity (m/s²), rho: air density (kg/m³),
# A: cross-sectional area (m²), C_D: drag coefficient,
# r: ball radius (m), omega0: initial angular velocity (rad/s)
p = [C₁.m, C₁.g, C₁.ρ, C₁.A, C₁.C_D, C₁.r, C₁.ω₀]

# Initial conditions.
# Here we assume the ball is kicked from the origin with an initial velocity.
# For example: initial position (0, 0, 0) and initial velocity (30, 0, 30) m/s.
dx₀ = [IC₁.v_x, IC₁.v_y, IC₁.v_z]
x₀ = [IC₁.x, IC₁.y, IC₁.z]

# Time span for the simulation
tspan = (0.0, 50.0)

# Define the ODE problem
prob = SecondOrderODEProblem(projectile!, dx₀, x₀, tspan, p)
sol = solve(prob, Tsit5())

# load image 
pitch = Makie.FileIO.load(expanduser("_posts/guides/interactive-blog/soccer_pitch.png"))

# soccer pitch size 
x_size = (0, 68)
y_size = (0, 105)
z_size = (0, 20)

# make a plot for the initial conditions and a field 
open(output_folder * "ode_ic.html", "w") do io
    sub = Session(session)
    app = App() do
        fig = Figure(size=(500, 500))
        ax = Axis3(fig[1, 1])
        p0 = Point3f(x₀)
        v0 = Vec3f(dx₀)

        xlims!(ax, x_size)
        ylims!(ax, y_size)
        zlims!(ax, z_size)
        arrows!(ax, [p0], [v0], color=:red)

        # set picture as xy plane
        surface!(ax, [0, 0, 68, 68], [0, 105, 105, 0], [0, 0, 0, 0], 
                    color=:lightgreen, transparency=true)

        fig
    end
    as_html(io, sub, app)
end
