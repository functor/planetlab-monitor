
source("functions.r")
cm <- read.csv('comon_analysis.txt', sep=',', header=TRUE)

planetlab_releases <- function (height) 
{
    h = height
    tstamp_20040412 <-abline_at_date("2004-04-12", col='white', lty=0, height=h)
    tstamp_20041112 <-abline_at_date("2004-11-12", col='grey60', lty=3, height=h)
    tstamp_20050301 <-abline_at_date("2005-03-01", col='grey60', lty=3, height=h)
    tstamp_20050615 <-abline_at_date("2005-06-15", col='white',  lty=0, height=h)
    tstamp_20051001 <-abline_at_date("2005-10-01", col='grey60', lty=3, height=h)
    tstamp_20060519 <-abline_at_date("2006-05-19", col='grey60', lty=3, height=h)
    tstamp_20070228 <-abline_at_date("2007-02-28", col='grey60', lty=3, height=h)
    tstamp_20070501 <-abline_at_date("2007-05-01", col='white',  lty=0, height=h)
    tstamp_20071021 <-abline_at_date("2007-10-21", col='grey60', lty=3, height=h)
    tstamp_20080601 <-abline_at_date("2008-06-01", col='grey60', lty=3, height=h)
    tstamp_20080815 <-abline_at_date("2008-08-15", col='white',  lty=0, height=h)
    tstamp_20090501 <-abline_at_date("2009-05-01", col='grey60', lty=3, height=h)
    tstamp_20100201 <-abline_at_date("2010-02-01", col='white',  lty=0, height=h)

    text(x=c(tstamp_20040412,
            tstamp_20041112,
            tstamp_20050301,
            tstamp_20050615,
            tstamp_20051001,
            tstamp_20060519,
            tstamp_20070228,
            tstamp_20071021,
            tstamp_20080601,
            tstamp_20090501),
         y=c(h),
         labels=c('Release', '3.0', '3.1', '', '3.2', '3.3', '4.0', '4.1', '4.2', '4.3')) 
}

# needs:
#   xlim=c(min_ts, max_ts)
#   labels = names
#   at = ts position
#   x
#   y
time_graph_setup <- function (from, to)
{
    # find 'type' range of days
    xlim <- c(tstamp(from, format="%Y/%m/%d"), tstamp(to, format="%Y/%m/%d"))

    date_months <-seq(as.Date(from), as.Date(to), 'month')
    date_years <-seq(as.Date(from), as.Date(to), 'year')
    month_str <- format(date_months, "%b")
    month_ts <- unclass(as.POSIXct(date_months))

    year_str <- format(date_years, "%Y")
    year_ts <- unclass(as.POSIXct(date_years))+180*60*60*24
        
    return (list(xlim=xlim, month_str=month_str, 
                 month_ts=month_ts, year_str=year_str, 
                 year_ts=year_ts))
}

tg <- time_graph_setup('2004/1/1', '2010/6/28')

#start_image("platform_availability.png")
par(mfrow=c(3,1))
# bottom, left, top, right margins
par(mai=c(0.2, 1, 0.3, 0.1))



plot(cm$ts, cm$total, type='l', col='grey60', 
        axes=F,
        xlab="",
        xlim=tg$xlim,
        ylim=c(0,1000),
        ylab="a) Online Node Count")
lines(cm$ts, cm$online, type='l', col='black' )

#axis(1, labels=tg$month_str, at=tg$month_ts, cex.axis=0.7)
#axis(1, tick=F, labels=tg$year_str, at=tg$year_ts, cex.axis=0.7, line=1)
axis(1, labels=c("","","","","","",""), at=tg$year_ts, cex.axis=0.7, line=-0.5)
axis(2, las=1)
planetlab_releases(1000)


par(mai=c(1, 1, 0.2, 0.1))

plot(cm$ts, log(cm$X2nd), type='l', col='grey75',
        axes=F,
        xlab="",
        xlim=tg$xlim,
        ylim=c(7,18), 
        ylab="b) Node Uptime by Quartile (days)")

axis(1, labels=tg$month_str, at=tg$month_ts, cex.axis=0.7)
axis(1, tick=F, labels=tg$year_str, at=tg$year_ts, cex.axis=0.7, line=1)
# TODO: change labels to days up, rather than log(days).
d<-c(.1,1,3.5,7,15,30,60,120,240)
axis(2, labels=d, at=log(d*60*60*24),las=1)

lines(cm$ts, log(cm$X3rd), col='black')
lines(cm$ts, log(cm$X4th), col='grey50')
#lines(cm$ts, log(cm$X5th), col='grey75')

abline(h=log(max(cm$X2nd[which(!is.na(cm$X2nd))])), col='grey80', lty=2)
abline(h=log(max(cm$X3rd[which(!is.na(cm$X3rd))])), col='grey80', lty=2)
abline(h=log(max(cm$X4th[which(!is.na(cm$X4th))])), col='grey80', lty=2)
#abline(h=log(max(cm$X5th[which(!is.na(cm$X5th))])), col='grey80', lty=2)
abline(h=log(7*60*60*24), col='grey80', lty=2)

planetlab_releases(18)

#end_image()
