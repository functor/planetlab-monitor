source("functions.r");


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



open_tickets <- function (t, from, to, type, fmt="%b")
{
    # find 'type' range of days
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, fmt)
    hbreaks<-unclass(as.POSIXct(dates))

    xx<-NULL;
    yy<-NULL;

    for ( i in seq(1,length(hbreaks)-1) )
    {
        # identify any tickets with a start time in range, lastreply in range
        # or where both start is less and lastreply is greater than the range
        t_sub <- t[which( (t$start < hbreaks[i] & t$lastreply > hbreaks[i+1]) | 
                          (t$start > hbreaks[i] & t$start <= hbreaks[i+1]) | 
                          (t$lastreply > hbreaks[i] & t$lastreply <= hbreaks[i+1]) ),]
        tickets <- length(t_sub$start)
        #if ( nrow(t_sub) > 0 ){
        #    for ( j in seq(1,nrow(t_sub)) )
        #    {
        #        #print(sprintf("id %s, date %s", t_sub[i,'ticket_id'], t_sub[i,'s1']))
        #        print(sprintf("id %s, date %s", t_sub[j,]$ticket_id, t_sub[j, 's1']))
        #    }
        #}

        xx<- c(xx, hbreaks[i])
        yy<- c(yy, tickets)

    }
    m<- months[1:length(months)-1]
    return (rbind(xx,yy,m))
}

online_nodes <- function (fb)
{
    breaks <- unique(fb$timestamp)
    n<-NULL
    o<-NULL
    x<-NULL
    for (i in seq(1,length(breaks)) )
    {
        ts <- breaks[i]
        sub <- fb[which(fb$timestamp == ts),]
        node_count   <- length(unique(sub$hostname))
        online_count <- length(unique(sub$hostname[which(sub$state=='BOOT')]))
        x<-c(x,ts)
        n<-c(n,node_count)
        o<-c(o,online_count)
    }
    print(length(x))
    print(length(n))
    print(length(o))
    return (rbind(x,n,o))
}

lowess_smooth <- function (x, y, delta=(60*60*24), f=0.02)
{
    a<-lowess(x, y, delta=delta, f=f)
    return (a);
}

#####

ns <- read.csv('node-status-jun09-feb10.csv', sep=',', header=TRUE)
an <- available_nodes(ns, "2009-06-10", "2010-02-28", 'day')

an_x<-an[1,][which(as.numeric(an[2,]) > 100)]
an_y<-an[2,][which(as.numeric(an[2,]) > 100)]


####
#fb7 <- read.csv('findbad_raw_2007.csv', sep=',', header=TRUE)
#fb8 <- read.csv('findbad_raw_2008.csv', sep=',', header=TRUE)
#fb9 <- read.csv('findbad_raw_2009.csv', sep=',', header=TRUE)

z7<- online_nodes(fb7)
z8<- online_nodes(fb8)
z9<- online_nodes(fb9)

zx <- c(z7[1,],z8[1,],z9[1,])
zy_reg <- c(z7[2,], z8[2,],z9[2,])
zy_avail <- c(z7[3,], z8[3,],z9[3,])

start_image("rt_aggregate_node_traffic.png")
par(mfrow=c(2,1))
par(mai=c(0,1,0.1,0.1))

a_reg<-lowess_smooth(zx, zy_reg)
plot(a_reg$x, a_reg$y, 
     ylim=c(0,700), xlim=c(min(x1), max(x1)), type='l', pch='.', axes=F,
     ylab="Online Node Count", xlab="")
       
sx <- zx[which(zy_avail > 330)]
sy <- zy_avail[which(zy_avail > 330)]
sx <- c(sx[1:2037],sx[2061:length(sx)])
sy <- c(sy[1:2037],sy[2061:length(sy)])

sx <- c(sx[1:1699],sx[1701:1707],sx[1709:length(sx)])
sy <- c(sy[1:1699],sy[1701:1707],sy[1709:length(sy)])

lines(sx, sy, col='grey80', pch='.')
lines(an_x, an_y, col='grey80', pch='.')

a_avail<-lowess_smooth(zx, zy_avail)
lines(a_avail$x, a_avail$y, col='red', pch='.')

a_avail_m3<-lowess_smooth(an_x, an_y)
lines(a_avail_m3$x, a_avail_m3$y, col='red', pch='.')

axis(2, las=1)

x_online_node_list <- c(tstamp("2004-6-1"), tstamp("2005-6-1"), tstamp("2006-6-1"), tstamp("2007-11-1"))
y_online_node_list <- c(330, 480,  500,  550)
lines(x_online_node_list, y_online_node_list, col='grey80')

#abline_at_date('2005-01-01', 'grey60')
#abline_at_date('2006-01-01', 'grey60')
#abline_at_date('2007-01-01', 'grey60')
#abline_at_date('2008-01-01', 'grey60')
#abline_at_date('2009-01-01', 'grey60')
#abline_at_date('2010-01-01', 'grey60')

tstamp_20041201 <-abline_at_date("2004-12-01", col='grey60', lty=2)
tstamp_20050301 <-abline_at_date("2005-03-01", col='grey60', lty=2)
tstamp_20050701 <-abline_at_date("2005-07-01", col='grey60', lty=2)
tstamp_20051101 <-abline_at_date("2005-11-01", col='grey60', lty=2)
tstamp_20051201 <-abline_at_date("2005-12-01", col='grey60', lty=2)
tstamp_20070101 <-abline_at_date("2007-01-01", col='grey60', lty=2)
tstamp_20070501 <-abline_at_date("2007-05-01", col='grey60', lty=2)
tstamp_20080601 <-abline_at_date("2008-06-01", col='grey60', lty=2)
tstamp_20080815 <-abline_at_date("2008-08-15", col='grey60', lty=2)
tstamp_20090501 <-abline_at_date("2009-05-01", col='grey60', lty=2)
tstamp_20100201 <-abline_at_date("2010-02-01", col='white', lty=2)


text(x=c( tstamp_20041201+(tstamp_20050301-tstamp_20041201)/2,
        tstamp_20050301+(tstamp_20050701-tstamp_20050301)/2,
        tstamp_20050701+(tstamp_20051101-tstamp_20050701)/2,
        tstamp_20051201+(tstamp_20070101-tstamp_20051201)/2,
        tstamp_20070101+(tstamp_20070501-tstamp_20070101)/2,
        tstamp_20080601+(tstamp_20080815-tstamp_20080601)/2,
        tstamp_20090501+(tstamp_20100201-tstamp_20090501)/2 ),
     y=c(700),
     labels=c('3.0', '3.1', '3.1S', '3.2', '4.0', '4.2', '4.3')) 

par(mai=c(1,1,0.1,0.1))
# system("parse_rt_data.py 3 > rt_data.csv");

t <- read.csv('rt_data_2004-2010.csv', sep=',', header=TRUE)
t2 <- t[which(t$complete == 1),]
ot <- open_tickets(t2, '2004/1/1', '2010/2/28', 'day', "%b")
x1<-as.numeric(ot[1,])
y1<-as.numeric(ot[2,])

a_ot<-lowess_smooth(x1, y1)

plot(x1, y1, col='grey80', type='l', axes=F, ylab="Open Tickets", xlab="Date") # , ylim=c(0,260))
lines(a_ot$x, round(a_ot$y), col='red')

axis(1, labels=ot[3,], at=ot[1,], cex.axis=0.7)
axis(2, las=1)
mtext("2004           2005           2006           2007           2008           2009", 1,2)

abline_at_date('2005-01-01', 'grey60')
abline_at_date('2006-01-01', 'grey60')
abline_at_date('2007-01-01', 'grey60')
abline_at_date('2008-01-01', 'grey60')
abline_at_date('2009-01-01', 'grey60')
abline_at_date('2010-01-01', 'grey60')
abline(h=25, lty=2, col='grey80')
abline(h=40, lty=2, col='grey80')
end_image()


m <- read.csv('rt_monitor_data.csv', sep=',', header=TRUE)
m2 <- m[which(m$complete == 1),]
otm <- open_tickets(m2, '2004/1/1', '2010/2/28', 'day', "%b")
xm<-as.numeric(otm[1,])
ym<-as.numeric(otm[2,])

a<-lowess(xm, ym, delta=(60*60*24), f=0.02)
x<-a$x
y<-a$y
lines(x, round(y), col='blue')

#end_image()
#t_july08 <-unclass(as.POSIXct("2008-07-01", origin="1970-01-01"))[1]
#breaks <- unique(fb8$timestamp[which(fb8$timestamp < t_july08)])
#fb8_boot <- fb8$timestamp[which(fb8$state=="BOOT" & fb8$timestamp < t_july08)]
#h8<-hist(fb8_boot, breaks=breaks[which(!is.na(breaks) & breaks!=0)])
#
#breaks <- unique(as.numeric(as.character(fb9$timestamp)))
#fb9_boot <- as.numeric(as.character(fb9$timestamp[which(fb9$state=="BOOT")]))
#hist(fb9_boot, breaks=breaks[which(!is.na(breaks) & breaks >= 1230775020)])

