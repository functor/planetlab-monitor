
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
x_end  <-unclass(as.POSIXct("2009-07-1", origin="1970-01-01"))[1]

par(mfrow=c(2,1))
par(mai=c(.9,.8,.2,.2))
#start_image("daily-node-count.png", height=400)
plot(dnc2$start[which(!is.na(dnc2$available))], dnc2$available[which(!is.na(dnc2$available))], 
    type='l', col='red', ylim=c(0,600), xlim=c(x_start, x_end),
    xlab="Date", ylab="Online Node Count", axes=F)

lines(dnc2$start[which(!is.na(dnc2$available) & dnc2$start > tstamp_0510 & dnc2$start <= tstamp_0815)], dnc2$available[which(!is.na(dnc2$available)& dnc2$start > tstamp_0510 & dnc2$start <= tstamp_0815)], type='l', col='green')

lines(dnc2$start[which(!is.na(dnc2$available) & dnc2$start > tstamp_1105 & dnc2$start <= tstamp_0223)], dnc2$available[which(!is.na(dnc2$available)& dnc2$start > tstamp_1105 & dnc2$start <= tstamp_0223)], type='l', col='blue')
#lines(dnc2$start[which(!is.na(dnc2$available))], dnc2$available[which(!is.na(dnc2$available))], 
#type='l', col='red', ylim=c(0,1000))
axis(2, las=1)
axis(1, cex.axis=0.7, labels=months, at=hbreaks)
       


#tstamp_0510 <-abline_at_date("2008-05-10", col='grey20', lty=0, height=570)
# dates takes from reboot_image() output for API events.
# green
tstamp_0610 <-abline_at_date("2008-06-10", col='grey20', lty=2, height=570)
tstamp_0815 <-abline_at_date("2008-08-15", col='grey70', lty=1, height=570)

# red
#tstamp_0905 <-abline_at_date("2008-09-05", col='grey70', height=570)
tstamp_0924 <-abline_at_date("2008-09-24", col='grey70', lty=1, height=570)
tstamp_1015 <-abline_at_date("2008-10-15", col='grey20', lty=2, height=570)
# blue
#tstamp_1105 <-abline_at_date("2008-11-05", col='white', lty=2, height=570)
#tstamp_1214 <-abline_at_date("2008-12-14", col='grey70', height=570)
tstamp_0223 <-abline_at_date("2009-02-23", col='grey70', height=570)
# red
#tstamp_0313 <-abline_at_date("2009-03-13", col='grey70', height=570)

#text(x=c(tstamp_0610+(tstamp_0815-tstamp_0610)/2,
#         tstamp_0815+(tstamp_0905-tstamp_0815)/2,
#         tstamp_0924+(tstamp_1015-tstamp_0924)/2, 
#         tstamp_1015+(tstamp_1214-tstamp_1015)/2, 
#         tstamp_1214+(tstamp_0223-tstamp_1214)/2, 
#         tstamp_0223+(tstamp_0313-tstamp_0223)/2), 
#     y=c(0),
#     labels=c("bug1", 'fix1', 'fix2', 'fix3', 'bug2', 'fix4')) #, 'fix 2', 'fix 3', 'fix 4'))

text(x=c(tstamp_0610,
         tstamp_0815,
         tstamp_0924),
     y=c(610),
     adj=c(1, 0.5),
     labels=c("bug1", 'fix1', 'fix2')) #, 'fix 2', 'fix 3', 'fix 4'))


text(x=c(tstamp_1015,
         tstamp_0223),
     adj=c(0, 0.5),
     y=c(610),
     labels=c('bug2', 'fix3')) #, 'fix 2', 'fix 3', 'fix 4'))

mtext("2008                                 2009", 1,2)
legend(unclass(as.POSIXct("2009-02-23", origin="1970-01-01"))[1], 200,
        cex=0.5,
        legend=c("Kernel Bug", "Notice Bug", "Typical MyOps", 'Bugs', 'Fixes'),
        pch=c('-', '-', '-'),
        col=c('green', 'blue', 'red', 'grey20', 'grey70'),
        lty=c(1, 1, 1, 2, 1), merge=T)

        #legend=c("Registered", "Online", 'Kernel Update', 'MyOps Event'),
        #pch=c('-', '-', '-', '-'),
        #col=c('blue', 'red', 'grey20', 'grey70'),
        #lty=c(1, 1, 2, 1), merge=T)

end_image()

