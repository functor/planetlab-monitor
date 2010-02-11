
source("functions.r");

# data collected from M2 pickle files
dnc <- read.csv('daily-available-node-count.csv', sep=',', header=TRUE)

dnc2<-add_timestamp(dnc)

tstamp_08 <-unclass(as.POSIXct("2008-05-07", origin="1970-01-01"))[1]
dnc2 <- dnc2[which( dnc2$start >  tstamp_08 ),]


dates <-seq(as.Date('2008-05-07'), as.Date('2009-05-07'), 'week')
months <- format(dates, "%b")
hbreaks<-unclass(as.POSIXct(dates))

x_start<-unclass(as.POSIXct("2008-05-07", origin="1970-01-01"))[1]
x_end  <-unclass(as.POSIXct("2009-06-1", origin="1970-01-01"))[1]

start_image("daily-node-count.png")
plot(dnc2$start[which(!is.na(dnc2$available))], dnc2$registered[which(!is.na(dnc2$available))], 
    type='l', col='blue', ylim=c(0,900), xlim=c(x_start, x_end),
    xlab="Date", ylab="Node Count", axes=F)
lines(dnc2$start[which(!is.na(dnc2$available))], dnc2$available[which(!is.na(dnc2$available))], type='l', col='red', ylim=c(0,900))
axis(2)
axis(1, labels=months, at=hbreaks)


tstamp_0610 <-abline_at_date("2008-06-10", col='grey20', lty=2)
# dates takes from reboot_image() output for API events.
tstamp_0815 <-abline_at_date("2008-08-15", col='grey20', lty=2)
tstamp_0905 <-abline_at_date("2008-09-05", col='grey70')
tstamp_0924 <-abline_at_date("2008-09-24", col='grey20', lty=2)
tstamp_1015 <-abline_at_date("2008-10-15", col='grey20', lty=2)
tstamp_1105 <-abline_at_date("2008-11-05", col='white', lty=2)
tstamp_1214 <-abline_at_date("2008-12-14", col='grey70')
tstamp_0223 <-abline_at_date("2009-02-23", col='grey70')
tstamp_0313 <-abline_at_date("2009-03-13", col='grey70')


text(x=c(tstamp_0610+(tstamp_0815-tstamp_0610)/2,
         tstamp_0815+(tstamp_0905-tstamp_0815)/2,
         tstamp_0924+(tstamp_1015-tstamp_0924)/2, 
         tstamp_1015+(tstamp_1105-tstamp_1015)/2, 
         tstamp_1214+(tstamp_0223-tstamp_1214)/2, 
         tstamp_0223+(tstamp_0313-tstamp_0223)/2), 
     y=c(0),
     labels=c("Kernel bug", 'fix1', 'fix2', 'fix3', 'Notice bug', 'fix4')) #, 'fix 2', 'fix 3', 'fix 4'))

legend(unclass(as.POSIXct("2009-03-13", origin="1970-01-01"))[1], 200,
        cex=0.7,
        legend=c("Registered", "Available", 'Kernel Update', 'MyOps Event'),
        pch=c('-', '-', '-', '-'),
        col=c('blue', 'red', 'grey20', 'grey70'),
        lty=c(1, 1, 2, 1), merge=T)

end_image()

