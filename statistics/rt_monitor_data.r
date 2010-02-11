

source("functions.r");

# system("parse_rt_data.py 22 > rt_monitor_data.csv");
m <- read.csv('rt_monitor_data.csv', sep=',', header=TRUE)

par(mfrow=c(2,1))

h<-hist(log(log(m$replies)), breaks=50)
lines(h$breaks[which(h$counts!=0)], h$counts[which(h$counts!=0)])
h<-hist(log(log(log(m$replies))), breaks=50)
lines(h$breaks[which(h$counts!=0)], h$counts[which(h$counts!=0)])


par(mfrow=c(1,1))

m2 <- m[which(m$complete == 1),]
d <- (m2$lastreply - m2$start)/(60*60)

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

d2<-(m2$lastreply-m2$start)
start_image("rt_monitor_ttc.png")
par(mfrow=c(2,1))
qqnorm(log(d2))
plot_rt_hist(m2)
end_image()

par(mfrow=c(1,1))
start_image("rt_monitor_trends.png")
hist(log(d2[which(d2>59026)]), breaks=60, xlab="LOG(time to last-reply)", main="Monitor Queue Traffic patterns")
end_image()

tstamp_78 <-unclass(as.POSIXct("2008-01-01", origin="1960-01-01"))[1]
tstamp_89 <-unclass(as.POSIXct("2009-01-01", origin="1960-01-01"))[1]

m_7 <- m2[which( m2$start < tstamp_78 ),]
m_8 <- m2[which( m2$start >= tstamp_78 & m2$start < tstamp_89 ),]
m_9 <- m2[which( m2$start >= tstamp_89 ),]


par(mfrow=c(3,1))
plot_rt_hist(m_7)
plot_rt_hist(m_8)
plot_rt_hist(m_9)
par(mfrow=c(1,1))


tstamp <-unclass(as.POSIXct("2008-01-01", origin="1960-01-01"))
m_67 <- m2[which( m2$start <  tstamp[1] ),]
m_89 <- m2[which( m2$start >= tstamp[1] ),]


#par(mfrow=c(2,1))
#plot_rt_hist(t_67)
#plot_rt_hist(t_89)
par(mfrow=c(1,1))
par(mai=c(1,1,1,2))
par(mar=c(5,4,4,8))

s_list <- c('2006'=1112, '2007'=1591, '2008'=1019, '2009'=815)
m_list <- c('2006'=0,    '2007'=119,  '2008'=229,  '2009'=251)

start_image('rt_aggregate_traffic.png')
par(mfrow=c(1,1))
par(mai=c(1,1,1,1))
par(mar=c(5,4,4,4))

s_list <- c(1519, 1596, 1112, 1591, 1019, 815)
m_list <- c(0,0,0,    119,  229,  251)
x_online_node_list <- c(1,   2.5,  4, 5.5, 7, 8.5)
y_online_node_list <- c(330, 480,  500,    550,  575,  642)

y<- rbind(support=s_list, monitor=m_list)
barplot(y, space=0.5, width=1, ylim=c(0,2000), xlim=c(0,9),  
        col=c('grey35', 'grey85'),
        legend=F, ylab="Messages with One or More Replies", xlab="Year")
scale_by <- 1500 / 700
lines(x_online_node_list, y_online_node_list*scale_by)
points(x_online_node_list, y_online_node_list*scale_by, pch=c(22))
ticks<-c(0, 100, 200, 300, 400, 500, 600, 700)

axis(1, labels=c('2004', '2005', '2006', '2007', '2008', '2009'), at=x_online_node_list)
axis(4, labels=ticks, at=ticks*scale_by)

mtext("Online Node Count", 4, line=3)
legend(6.5, 2000, 
        cex=0.7,
        legend=c("Online Node Count", "MyOps Messages", "Support Messages"), 
         fill=c(0, 'grey85', 'grey40'),
        lty=c(1,0,0), merge=T)
end_image()


start_image("rt_monitor_seasonal.png")
par(mfrow=c(3,1))
par(mai=c(.3,.3,.3,.3))
year_hist(m_7, "2007", "2006/12/31", "2008/1/7", 60)
year_hist(m_8, "2008", "2007/12/30", "2009/1/7", 60)
year_hist(m_9, "2009", "2008/12/28", "2010/1/30", 60)
end_image()

par(mfrow=c(1,1))
