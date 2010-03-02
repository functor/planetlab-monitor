source("functions.r");

# data collected from M3 fb db 
# system("./harvest_nodestatus.py  > node-status-jun09-feb10.csv")
ns <- read.csv('node-status-jun09-feb10.csv', sep=',', header=TRUE)

available_nodes <- function (ns, from, to, type, fmt="%b")
{
    # find 'type' range of days
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, fmt)
    hbreaks<-unclass(as.POSIXct(dates))

    xx<-NULL;
    yy<-NULL;

    for ( i in seq(1,length(hbreaks)-1) )
    {
        # get range from ns
        ns_sub <- ns[which(ns$date > hbreaks[i] & ns$date <= hbreaks[i+1] & ns$status == 'BOOT'),]
        nodes <- length(ns_sub$date)

        xx<- c(xx, hbreaks[i])
        yy<- c(yy, nodes)

    }
    m<- months[1:length(months)-1]
    return (rbind(xx,yy,m))
}

an <- available_nodes(ns, "2009-06-10", "2010-02-28", 'day')

x_start<-unclass(as.POSIXct("2009-06-10", origin="1970-01-01"))[1]
x_end  <-unclass(as.POSIXct("2010-02-28", origin="1970-01-01"))[1]

par(mfrow=c(1,1))
par(mai=c(.9,.8,.5,.4))
#start_image("daily-node-count.png")
sx<-an[1,][which(as.numeric(an[2,]) > 100)]
sy<-an[2,][which(as.numeric(an[2,]) > 100)]
plot(sx, sy,
    type='l', col='blue', ylim=c(0,1000), xlim=c(x_start, x_end),
    xlab="Date", ylab="Node Count", axes=F)
axis(2, las=1)
axis(1, labels=months, at=hbreaks)


