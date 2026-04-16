#let vm = $upright(v)_m$ 
#let vr = $upright(v)_r$ 
#let an = $omega$ 
= Calculating step timing for a trapezoidal acceleration curve
== Parameters
there are a few necessary parameters for calculating the delay between steps.\
angular acceleration: $an$ \
steps per revolution: $m$ \
max angular velocity: $vm$ \
total distance: $d$
== initial case - maximum velocity is reached
We will first handle the case where maximum velocity is reached before the half way point.\
we know that:
$
theta = 1/2 an t ^2 $
from which we can derive that 
$
  t(theta) = sqrt((2 theta ) /an)
$
this is our function for the time of each step when the motor is accelerating.

to find when we have reached the maximum velocity we need only:
$
  &vm = an t(theta_1) = an sqrt((2 theta_1 ) /an) = sqrt(2 an theta) \ 
  &theta_1 = vm^2/(2an)
$ 
because we know the distance from the beginning we can use the fact this is the inverse
of decellerating to also say that: we must start decellerating at 
$ 
  theta_2 = (d - vm^2/(2an) ) 
$ 
when we are moving at a constant velocity our timing is given by:
$
 theta (t) &= vm(t - t_1) + theta_1\ 
 &= vm t - vm vm/(an) + vm^2/(2an) \ 
 &= vm ( t - vm/(2an)) \ 
  t_c (theta) &= theta / vm + vm / (2an) 
$
#pagebreak()
To find the timing function for the deceleration stage we need end time of the move. This may seem initially
complicated, but we have a convenient symmetry: deceleration takes the same time as acceleration.
$
  t_f = & t_c (theta_2) + t_1 \

  = & t_c (d - vm^2/(2an)) + vm/an \
  = & ((d - vm^2/(2an) )/ vm + vm/(2an)) + vm/an = d/vm - vm/(2 an) + vm/an\
  = & d/vm + vm/(2an) \
$
giving us the final deceleration function:
$
  t_d (theta) = (t_f - sqrt((2(theta_f - theta))/an))
$
thus we can define the peicewise function:
$
               theta lt.eq & theta_1 &: t(theta) = & sqrt((2 theta)/an  ) \
   theta_1 lt  theta lt.eq & theta_2 &: t(theta) = & theta / vm + vm/(2an)\
   theta_2 lt  theta lt.eq & d       &: t(theta) = & (t_f - sqrt((2(theta_f - theta))/an))\

$
== second case - short hop
if $ d < vm^2/(2an) $ then we have the case that the maximum velocity is never reached. Though in this case
we do gain the simplification that there is no constant velocity section, this simplifies our $t_f$ calculation.
our first function does not change, our second function is erased, and the only thing that changes in the third 
is how we define $t_f$. our positional limits also change, we now only need one of them: $theta_1 = d/2$, where 
we go from accelerating to decellerating.
$
  & d/2 = 1/2 an t_1 ^2 & d = an t_1^2  \
  & t_1 = sqrt(d/an) \ 
  & t_f = 2 t_1 = 2 sqrt(d/an)\
$
so we end up with essentially the same functions, however with the values subbed in we get:
$
              theta lt.eq & d/2 &: t(theta) = & sqrt((2 theta)/an  ) \
  theta_1 lt  theta lt.eq & d       &: t(theta) = & (2 sqrt(d/an) - sqrt((2(theta_f - theta))/an))\
$




