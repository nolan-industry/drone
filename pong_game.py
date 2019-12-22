import turtle

wn = turtle.Screen()
wn.title("ponggame")
wn.bgcolor("blue")
wn.setup(width=800, height=600)
wn.tracer(0)

#score
score_a = 0
score_b = 0
#paddle A
p_a = turtle.Turtle()
p_a.speed(0)
p_a.shape("circle")
p_a.color("white")
p_a.penup()
p_a.goto(-350,0)
p_a.shapesize(stretch_wid=5, stretch_len=1)
#paddle B
p_b = turtle.Turtle()
p_b.speed(0)
p_b.shape("circle")
p_b.color("white")
p_b.penup()
p_b.goto(350,0)
p_b.shapesize(stretch_wid=5, stretch_len=1)
#ball
ball = turtle.Turtle()
ball.speed(0)
ball.shape("circle")
ball.color("white")
ball.penup()
ball.goto(0,0)
ball.dx = 0.01
ball.dy = 0.01

#pen
pen = turtle.Turtle()
pen.speed(0)
pen.color("white")
pen.penup()
pen.hideturtle()
pen.goto(0, 260)
pen.write("player A: {}  player B: {}" .format(score_a, score_b), align="center", font=("Courier", 24, "normal"))

#Function
def p_a_up():
    y = p_a.ycor()
    y += 20
    p_a.sety(y)

def p_a_down():
    y = p_a.ycor()
    y -= 20
    p_a.sety(y)
def p_a_cheat():
    p_a.shapesize(stretch_wid=50, stretch_len=1)
def p_a_uncheat():
    p_a.shapesize(stretch_wid = 5, stretch_len = 1)

#keyboard binding
wn.listen()
wn.onkeypress(p_a_up, "w")
wn.onkeypress(p_a_down, "s")
wn.onkeypress(p_a_cheat, "y")
wn.onkeypress(p_a_uncheat, "u")
#Function
def p_b_up():
    y = p_b.ycor()
    y += 20
    p_b.sety(y)

def p_b_down():
    y = p_b.ycor()
    y -= 20
    p_b.sety(y)

#keyboard binding
wn.listen()
wn.onkeypress(p_b_up, "Up")
wn.onkeypress(p_b_down, "Down")


while True:
    wn.update()
    #move the ball
    ball.setx(ball.xcor() + ball.dx)
    ball.sety(ball.ycor() + ball.dy)

    #border check
    if ball.ycor() > 290:
        ball.sety(290)
        ball.dy *= -1

    if ball.ycor() < -290:
        ball.sety(-290)
        ball.dy *= -1

    if ball.xcor() > 390:
        ball.goto(0,0)
        ball.dx *=-1
        score_a +=1
        pen.clear()
        pen.write("player A: {}  player B: {}".format(score_a, score_b), align="center", font=("Courier", 24, "normal"))
    if ball.xcor() < -390:
        ball.goto(0,0)
        ball.dx *=-1
        score_b +=1
        pen.clear()
        pen.write("player A: {}  player B: {}".format(score_a, score_b), align="center", font=("Courier", 24, "normal"))

    #paddle and ball collision
    if (ball.xcor() > 340 and ball.xcor() < 350 and ball.ycor() < p_b.ycor() + 40 and ball.ycor() > p_b.ycor() - 40):
        ball.setx(340)
        ball.dx *= -1
    if (ball.xcor() < -340 and ball.xcor() > -350 and ball.ycor() < p_a.ycor() + 40 and ball.ycor() > p_a.ycor() - 40):
        ball.setx(-340)
        ball.dx *= -1