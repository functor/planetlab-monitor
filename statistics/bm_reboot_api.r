
source("functions.r");

# system("parse_rt_data.py > rt_data.csv");
# ./bmevents.py events.1-18-10 BootUpdateNode > bm_reboot_2010-01-18.csv
# ./bmevents.py events.10-08-09 BootUpdateNode > bm_reboot_2009-10-08.csv 
# ./bmevents.py events.29.12.08.dump BootUpdateNode > bm_reboot_2008-12-29.csv
# ./bmevents.py events.8-25-09.dump BootUpdateNode > bm_reboot_2009-08-25.csv
# 
t <- read.csv('bm_reboot_2008-12-29.csv', sep=',', header=TRUE)

t2<-t

tstamp_78 <-unclass(as.POSIXct("2008-01-01", origin="1960-01-01"))[1]
tstamp_89 <-unclass(as.POSIXct("2009-01-01", origin="1960-01-01"))[1]

t_7 <- t2[which( t2$start < tstamp_78 ),]
t_8 <- t2[which( t2$start >= tstamp_78 & t2$start < tstamp_89 ),]
t_9 <- t2[which( t2$start >= tstamp_89 ),]

tstamp <-unclass(as.POSIXct("2008-01-01", origin="1960-01-01"))
t_67 <- t2[which( t2$start <  tstamp[1] ),]
t_89 <- t2[which( t2$start >= tstamp[1] ),]

start_image("bm_reboot_api.png")

par(mfrow=c(2,1))
par(mai=c(.5,.4,.5,.4))
year_hist(t_9, "2009", "2009/06/21", "2010/2/10", 500, 'day', "Daily Reboot Rates")
rows_api <- year_hist_unique(t_9, "2009", "2009/06/21", "2010/2/10", 100, 'day', "Unique Daily Reboots")

#year_hist(t_89, "2008-2009", "2008/01/21", "2010/2/10", 0, 'day', "Daily Reboot Rates")
#rows <- year_hist_unique(t_89, "2008-2009", "2008/01/21", "2010/2/10", 0, 'day', "Unique Daily Reboots")

end_image()


## NOTE: compare api and log data:
start_image("bm_reboot_compare.png", width=960)
par(mfrow=c(1,1))
par(mai=c(1.0,.7,.7,.7))
x<- cbind(rows$reboots, rows_api$reboots)
#barplot(t(x), beside=TRUE, ylim=c(0,150), main="Compare Daily Frequency of Raw-logs & API Events")
barplot(rows$reboots-rows_api$reboots, ylim=c(-40,150), main="Difference between Raw-logs & API Events", xlab="Day", ylab="Difference of Frequency")
end_image()

# it appears that logs come out ahead consistently of the API events.
start_image("bm_reboot_diff_freq.png")
d<-rows$reboots-rows_api$reboots
hist(d[which( d > -10 & d < 20)], breaks=20, main="Frequency of Differences", xlab="Difference")
end_image()

# * why is this so?

###

start_image("reboot_distributions.png")
par(mfrow=c(2,1))
par(mai=c(.5,.5,.5,.5))

m<-mean(rows$reboots[which(rows$reboots>0&rows$reboots<50)])
s<-sd(rows$reboots[which(rows$reboots>0&rows$reboots<50)])

qqnorm(rows$reboots[which(rows$reboots>0&rows$reboots<50)])
qqline(rows$reboots[which(rows$reboots>0&rows$reboots<50)])

h<-hist(rows$reboots[which(rows$reboots>0&rows$reboots<50)], breaks=20)
x<- 0:100/100 * 2 * m
y<- dnorm(x, mean=m, sd=s)
lines(x,y*max(h$counts)/max(y))
end_image()

par(mfrow=c(1,1))
par(mai=c(.7,.7,.7,.7))
