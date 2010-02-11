

source("functions.r");

# system("parse_rt_data.py 3 > rt_data.csv");
#t <- read.csv('rt_data.csv', sep=',', header=TRUE)
t <- read.csv('rt_data_2004-2010.csv', sep=',', header=TRUE)

par(mfrow=c(2,1))

h<-hist(log(log(t$replies)), breaks=50)
lines(h$breaks[which(h$counts!=0)], h$counts[which(h$counts!=0)])
h<-hist(log(log(log(t$replies))), breaks=50)
lines(h$breaks[which(h$counts!=0)], h$counts[which(h$counts!=0)])


par(mfrow=c(1,1))

t2 <- t[which(t$complete == 1),]
d <- (t2$lastreply - t2$start)/(60*60)

#start_image("rt_hist_ttc_1000.png")
#hist(d[which(d<1000)], xlab="hours from creation to last reply", breaks=30)
#end_image()
#
#start_image("rt_hist_ttc_200.png")
#hist(d[which(d<200)], xlab="hours from creation to last reply", breaks=30)
#end_image()
#
#start_image("rt_hist_ttc_50.png")
#hist(d[which(d<50)], xlab="hours from creation to last reply", breaks=30)
#end_image()
#
#start_image("rt_hist_ttc_10.png")
#hist(d[which(d<10)], xlab="hours from creation to last reply", breaks=30)
#end_image()
#
#d2 <- (t2$lastreply - t2$start)
#h<-hist(log(d2), plot=F, breaks=50)
#lines(h$breaks[which(h$counts!=0)], h$counts[which(h$counts!=0)])


# this doesn't work as I would like.  I think the bins aren't as I expect
#h <- hist(d, plot=F, breaks=c(seq(0,max(d)+1, .1)))
#plot(h$counts, log="x", pch=20, col="blue",
#	main="Log-normal distribution",
#	xlab="Value", ylab="Frequency")

#plot(log(d2))
#plot(ecdf(d2))

tstamp_45 <-unclass(as.POSIXct("2005-01-01", origin="1960-01-01"))[1]
tstamp_56 <-unclass(as.POSIXct("2006-01-01", origin="1960-01-01"))[1]
tstamp_67 <-unclass(as.POSIXct("2007-01-01", origin="1960-01-01"))[1]
tstamp_78 <-unclass(as.POSIXct("2008-01-01", origin="1960-01-01"))[1]
tstamp_89 <-unclass(as.POSIXct("2009-01-01", origin="1960-01-01"))[1]
tstamp_90 <-unclass(as.POSIXct("2010-01-01", origin="1960-01-01"))[1]


t_4 <- t2[which( t2$start <  tstamp_45 ),]
t_5 <- t2[which( t2$start >= tstamp_45 & t2$start < tstamp_56 ),]
t_6 <- t2[which( t2$start >= tstamp_56 & t2$start < tstamp_67 ),]
t_7 <- t2[which( t2$start >= tstamp_67 & t2$start < tstamp_78 ),]
t_8 <- t2[which( t2$start >= tstamp_78 & t2$start < tstamp_89 ),]
t_9 <- t2[which( t2$start >= tstamp_89 & t2$start < tstamp_90 ),]
t_10 <- t2[which( t2$start >= tstamp_90 ),]

par(mfrow=c(4,1))
plot_rt_hist(t_4)
plot_rt_hist(t_5)
plot_rt_hist(t_6)
plot_rt_hist(t_7)
plot_rt_hist(t_8)
plot_rt_hist(t_9)
par(mfrow=c(1,1))

start_image("rt_support_seasonal.png")
par(mfrow=c(6,1))
par(mai=c(.3,.3,.3,.3))

# start dates on Sunday to align all weeks with weekend boundaries.
year_hist(t_4, "2004", "2003/12/28", "2005/1/7", 85)
year_hist(t_5, "2005", "2005/1/2", "2006/1/7", 85)
year_hist(t_6, "2006", "2006/1/1", "2007/1/7", 85)
year_hist(t_7, "2007", "2006/12/31", "2008/1/7", 85)
year_hist(t_8, "2008", "2007/12/30", "2009/1/7", 85)
year_hist(t_9, "2009", "2008/12/28", "2010/1/30", 85)
end_image()

par(mai=c(0.7,0.7,0.7,0.7))
par(mfrow=c(1,1))


tstamp <-unclass(as.POSIXct("2008-01-01", origin="1960-01-01"))
t_67 <- t2[which( t2$start <  tstamp[1] ),]
t_89 <- t2[which( t2$start >= tstamp[1] ),]


# install.packages('sn')
require(sn)
par(mfrow=c(6,1))
par(mai=c(0.3,0.3,0.3,0.3))

#start_image("rt_hist_ttc_1000.png")
time_hist <- function (t, lessthan, year, log=T, breaks=30, xlim=c(-4,10), ylim=c(0,150))
{
    d <- (t$lastreply - t$start)/(60*60)
    main = sprintf("Histogram of d<%s for %s", lessthan, year);
    if ( log )
    {
        d <- log(d[which(d<lessthan)])
        avg <- round(mean(d), 2)
        main = sprintf("Histogram of d<%s for %s : %s", lessthan, year, avg);
        #h<-sn.mle(d, xlab="Hours to Complete Ticket", breaks=30, main=main, xlim=xlim, ylim=ylim)
        h<-sn.mle(y=d)
    } else {
        h<-hist(d[which(d<lessthan)], xlab="Hours to Complete Ticket", breaks=30, main=main, xlim=xlim, ylim=ylim)
    }
    return (h);
}
tstamp <-unclass(as.POSIXct("2007-05-01", origin="1960-01-01"))
t_7a <- t_7[which(t_7$start < tstamp),]
t_7b <- t_7[which(t_7$start >= tstamp),]

#end_image()
h4<-time_hist(t_4, 10000, "2004")
h5<-time_hist(t_5, 10000, "2005")
h6<-time_hist(t_6, 10000, "2006")
#h7<-time_hist(t_7, 10000, "2007")
h7a<-time_hist(t_7a, 10000, "2007")
h7b<-time_hist(t_7b, 10000, "2007")
h8<-time_hist(t_8, 10000, "2008")
h9<-time_hist(t_9, 10000, "2009")

tstamp <-unclass(as.POSIXct("2009-09-01", origin="1960-01-01"))
m_9a <- m_9[which(m_9$start < tstamp),]
m_9b <- m_9[which(m_9$start >= tstamp),]

split_by_time <- function (t, datestr)
{
    tstamp <-unclass(as.POSIXct(datestr, origin="1960-01-01"))
    a <- t[which(t$start < tstamp),]
    b <- t[which(t$start >= tstamp),]
    v<- list('before'=a, 'after'=b)
    return (v);
}

mh7 <- time_hist(m_7, 10000, '2007')

sm_8 <- split_by_time(m_8, "2008-07-01")
#mh8a <- time_hist(rbind(m_7, m_8$before, m_8$after), 10000, '2008')
#mh8a <- time_hist(rbind(m_7[which(log((m_7$lastreply-m_7$start)/(60*60))>2),]), 10000, '2008')
# m_7 is junk data

mh_8 <- time_hist(sm_8$before, 10000, '2008')

sm_9 <- split_by_time(m_9, "2009-09-01")

mh_89 <- time_hist(rbind(sm_8$after, sm_9$before), 10000, '2009')
mh_9 <- time_hist(sm_9$after, 10000, '2009')


x<-seq(-8,10,0.01)
#x<- exp(x)/24

#my7<-dsn(x, dp=cp.to.dp(mh7$cp))
my8<-dsn(x, dp=cp.to.dp(mh_8$cp))
my89<-dsn(x, dp=cp.to.dp(mh_89$cp))
my9<-dsn(x, dp=cp.to.dp(mh_9$cp))

y4<-dsn(x, dp=cp.to.dp(h4$cp))
y5<-dsn(x, dp=cp.to.dp(h5$cp))
y6<-dsn(x, dp=cp.to.dp(h6$cp))
y7a<-dsn(x, dp=cp.to.dp(h7a$cp))
y7b<-dsn(x, dp=cp.to.dp(h7b$cp))
y8<-dsn(x, dp=cp.to.dp(h8$cp))
y9<-dsn(x, dp=cp.to.dp(h9$cp))

start_image("rt_time_to_resolve.png")
par(mfrow=c(1,1))
par(mai=c(1.0,0.7,0.7,0.7))
# monitor
plot(x, my9, col='blue', type='l', axes=F, xlab="Days to Resolve", ylab="Density")
axis(1, labels=c(0.0001, 0.01, 0.1, 1, 5, 20, 100), at=c(0.0001, 0.01, 0.1, 1, 5, 20, 100))
axis(2)
lines(x, my8, col='dodgerblue')
lines(x, my7, col='turquoise')
abline(v=x[which(my8==max(my8))])
abline(v=x[which(my9==max(my9))])

# heavy
lines(x, y7a, col='green3')
lines(x, y4, col='green4')
lines(x, y5, col='greenyellow')

abline(v=x[which(y4==max(y4))])
abline(v=x[which(y5==max(y5))])
abline(v=x[which(y7a==max(y7a))])

# light
lines(x, y7b, col='orange', type='l')
lines(x, y6, col='orange3')
lines(x, y8, col='firebrick2')
lines(x, y9, col='firebrick4')

abline(v=x[which(y7b==max(y7b))])
abline(v=x[which(y6==max(y6))])
abline(v=x[which(y8==max(y8))])
abline(v=x[which(y9==max(y9))])

end_image()

whisker <- function (x0,y0,sd, length=0.05)
{
    arrows(x0, y0, x0, y0+sd, code=2, angle=90, length=length)
    arrows(x0, y0, x0, y0-sd, code=2, angle=90, length=length)
}

whisker2 <- function (x0,y0, y0_high, y0_low, col="black", length=0.05)
{
    arrows(x0, y0, x0, y0_high, code=2, angle=90, length=length, col=col)
    arrows(x0, y0, x0, y0_low, code=2, angle=90, length=length, col=col)
}

start_image("rt_aggregate_times.png")
par(mfrow=c(1,1))
par(mai=c(1,1,1,1))
par(mar=c(5,4,4,4))

s_list <- c(1519, 1596, 1112, 1591, 1019, 815)
m_list <- c(0,0,0,    119,  229,  251)
x_tick_list <- c(1,   2.5,  4, 5.5, 7, 8.5)
x_tt_resolve_list <- c(1,   2.5,  4, 5.2,5.8, 7, 8.5)
y_tt_resolve_list <- c( x[which(y4==max(y4))],
                            x[which(y5==max(y5))],
                            x[which(y6==max(y6))],
                            x[which(y7a==max(y7a))],
                            x[which(y7b==max(y7b))],
                            x[which(y8==max(y8))],
                            x[which(y9==max(y9))])


y_mean_list <- c( h4$cp['mean'],
                h5$cp['mean'],
                h6$cp['mean'],
                h7a$cp['mean'],
                h7b$cp['mean'],
                h8$cp['mean'],
                h9$cp['mean'])

y_sd_list <- c( h4$cp['s.d.'],
                h5$cp['s.d.'],
                h6$cp['s.d.'],
                h7a$cp['s.d.'],
                h7b$cp['s.d.'],
                h8$cp['s.d.'],
                h9$cp['s.d.'])

days_tt_resolve <- exp(y_tt_resolve_list)/24
days_tt_resolve_low <- exp(y_tt_resolve_list-y_sd_list)/24
days_tt_resolve_high <- exp(y_tt_resolve_list+y_sd_list)/24


my_mean_list <- c( mh_8$cp['mean'],
                mh_89$cp['mean'],
                mh_9$cp['mean'])

my_sd_list <- c( mh_8$cp['s.d.'],
                mh_89$cp['s.d.'],
                mh_9$cp['s.d.'])

mx_tt_resolve_list <- c(7, 8, 8.5)
my_tt_resolve_list <- c(x[which(my8==max(my8))],
                        x[which(my89==max(my89))],
                        x[which(my9==max(my9))] )

mdays_tt_resolve <- exp(my_tt_resolve_list)/24
mdays_tt_resolve_low <- exp(my_tt_resolve_list-my_sd_list)/24
mdays_tt_resolve_high <- exp(my_tt_resolve_list+my_sd_list)/24


days_y_sd_list <- exp(y_sd_list)/24
mdays_y_sd_list <- exp(my_sd_list)/24

days_y_sd_list <- exp(y_sd_list)/24
mdays_tt_resolve <- exp(my_tt_resolve_list)/24

plot(x_tt_resolve_list, days_tt_resolve, type='p', pch=c(22), axes=FALSE, 
        log='y', ylim=c(.01,350), xlab="Year", ylab='')
#points(x_tt_resolve_list, days_tt_resolve, pch=c(22))

lines(c(x_tt_resolve_list[1:2], x_tt_resolve_list[4]), c(days_tt_resolve[1:2], days_tt_resolve[4]), col='red')
lines(c(x_tt_resolve_list[3], x_tt_resolve_list[5:7]), c(days_tt_resolve[3], days_tt_resolve[5:7]), col='green')
#lines(mx_tt_resolve_list, mdays_tt_resolve)
#points(mx_tt_resolve_list, mdays_tt_resolve, pch=c(24))

lines(mx_tt_resolve_list, mdays_tt_resolve, col='blue')
points(mx_tt_resolve_list, mdays_tt_resolve, pch=c(24))

ticks<-c(0,0.01, 0.1, 0.5,1,2,4,7,21, 28, 7*8, 7*16)

axis(1, labels=c('2004', '2005', '2006', '2007', '2008', '2009'), at=x_tick_list)
axis(2, labels=ticks, at=ticks)
mtext("Days to Resolve Message", 2, line=3)
#axis(2, labels=ticks, at=ticks)
#for (i in 1:length(days_y_sd_list) ) {
#    whisker(x_tt_resolve_list[i], days_tt_resolve[i], days_y_sd_list[i])
#}
#for (i in 1:length(mdays_y_sd_list) ) {
#    whisker(mx_tt_resolve_list[i], mdays_tt_resolve[i], mdays_y_sd_list[i])
#}
for (i in c(1,2,4) ) {
    whisker2(x_tt_resolve_list[i], days_tt_resolve[i], 
            days_tt_resolve_high[i], days_tt_resolve_low[i], col='red')
}
for (i in c(3,5,6,7) ) {
    whisker2(x_tt_resolve_list[i], days_tt_resolve[i], 
            days_tt_resolve_high[i], days_tt_resolve_low[i], col='green')
}
for (i in 1:length(mdays_y_sd_list) ) {
    whisker2(mx_tt_resolve_list[i], mdays_tt_resolve[i], 
            mdays_tt_resolve_high[i], mdays_tt_resolve_low[i], col='blue')
}

abline(h=21,col='grey90')
abline(h=2,col='grey90')
abline(h=0.5,col='grey80')

legend(1, .05, 
        cex=0.7,
        legend=c("Unstable Periods", "Stable Periods", "MyOps Messages"), 
        pch=c(22, 22, 24),
        col=c('red', 'green', 'blue'),
        lty=c(1, 1,1), merge=T)
end_image()
# install.packages('UsingR')
require(UsingR)

m<-min(t_4$start)
d<-data.frame(
    '2004'=t_4$start-m,
    '2005'=t_5$start-m,
    '2006'=t_6$start-m)
simple.violinplot(d)

par(mfrow=c(3,3))
par(mai=c(.3,.3,.3,.3))
sp <- function (t)
{
    d <- (t$lastreply-t$start)/(60*60*24)
    simple.violinplot(log(d))
}
sp(t_4)
sp(t_5)
sp(t_6)
sp(t_7)
sp(t_8)
sp(t_9)
sp(m_8)
sp(m_89)
sp(m_9)


t3 <- add_year (t2)
m3 <- add_year (m2)

par(mfrow=c(1,2))
par(mai=c(.5,.5,.5,.5))
t4<-t3[which((t3$lastreply-t3$start)/(60*60*24) < 20),]
t4<-t3
simple.violinplot(log((lastreply-start)/(60*60*24)) ~ year, data=t4)

m3[which((m3$lastreply-m3$start)< 0),]
m4<-m3[which((m3$lastreply-m3$start)/(60*60*24) < 100),]
simple.violinplot(log((lastreply-start)/(60*60*24)) ~ year, data=m4, log='y')

meanof <- function (t, year)
{
    tx <- t[which(t$year == year),]
    r<-sn.em(y=log((tx$lastreply-tx$start)/(60*60*24)))
    return (r)
}

t_sd <- p
t_p <- c( meanof(t3,2004)$cp['mean'],
        meanof(t3,2005)$cp['mean'],
        meanof(t3,2006)$cp['mean'],
        meanof(t3,2007)$cp['mean'],
        meanof(t3,2008)$cp['mean'],
        meanof(t3,2009)$cp['mean'],
        meanof(t3,2010)$cp['mean'])
points(t_p)
for (i in 1:length(t_sd) ) {
    whisker(i, t_p[i], exp(t_sd[i]))
}






#for (i in 1:length(y_tt_resolve_list) ) { 
#    whisker(x_tt_resolve_list[i], scale_by*y_tt_resolve_list[i], scale_by*2) 
#}
#for (i in 1:length(my_tt_resolve_list) ) { 
#    whisker(mx_tt_resolve_list[i], scale_by*my_tt_resolve_list[i], scale_by*2) 
#}

#
#end_image()
#par(mfrow=c(2,1))
#plot_rt_hist(t_67)
#plot_rt_hist(t_89)
par(mfrow=c(1,1))

