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
#fball <- rbind(fb7,fb8,fb9)

z7<- online_nodes(fb7)
z8<- online_nodes(fb8)
z9<- online_nodes(fb9)

zx <- c(z7[1,],z8[1,],z9[1,])
zy_reg <- c(z7[2,], z8[2,],z9[2,])
zy_avail <- c(z7[3,], z8[3,],z9[3,])

start_image("node_availability.png")
par(mfrow=c(2,1))
par(mai=c(0.1,1,0.1,0.1))

a_reg<-lowess_smooth(zx, zy_reg)
plot(a_reg$x, a_reg$y, 
     ylim=c(0,700), xlim=c(min(x1[length(x1)/2]), max(x1)), type='l', pch='.', axes=F,
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

tstamp_20041112 <-abline_at_date("2004-11-12", col='grey60', lty=2)
tstamp_20050301 <-abline_at_date("2005-03-01", col='grey60', lty=2)
tstamp_20050615 <-abline_at_date("2005-06-15", col='grey60', lty=2)
tstamp_20051023 <-abline_at_date("2005-10-23", col='grey60', lty=2)
tstamp_20070101 <-abline_at_date("2007-01-01", col='grey60', lty=2)
tstamp_20070501 <-abline_at_date("2007-05-01", col='grey60', lty=2)
tstamp_20080601 <-abline_at_date("2008-06-01", col='grey60', lty=2)
tstamp_20080815 <-abline_at_date("2008-08-15", col='grey60', lty=2)
tstamp_20090501 <-abline_at_date("2009-05-01", col='grey60', lty=2)
tstamp_20100201 <-abline_at_date("2010-02-01", col='white', lty=2)


text(x=c( tstamp_20041112+(tstamp_20050301-tstamp_20041112)/2,
        tstamp_20050301+(tstamp_20050615-tstamp_20050301)/2,
        tstamp_20050615+(tstamp_20051023-tstamp_20050615)/2,
        tstamp_20051023+(tstamp_20070101-tstamp_20051023)/2,
        tstamp_20070101+(tstamp_20070501-tstamp_20070101)/2,
        tstamp_20080601+(tstamp_20080815-tstamp_20080601)/2,
        tstamp_20090501+(tstamp_20100201-tstamp_20090501)/2 ),
     y=c(700),
     labels=c('3.0', '3.1', '3.1S', '3.2', '4.0', '4.2', '4.3')) 


l<-length(ot[3,])
#axis(1, labels=ot[3,l/2:l], at=ot[1,l/2:l], cex.axis=0.7)
#axis(2, las=1)
#mtext("2004           2005           2006           2007           2008           2009", 1,2)

uptime_nodes_m3 <- function (uh, from, to)
{
    # find 'type' range of days
    dates <-seq(as.Date(from), as.Date(to), 'day')
    months <- format(dates, '%b')
    hbreaks<-unclass(as.POSIXct(dates))

    xx<-NULL;
    yy<-NULL;
    date_index <- NULL;
    q_list <- NULL;

    print(length(hbreaks))

    for ( i in seq(1,length(hbreaks)-1) )
    {
        print (sprintf("round %s of %s", i, length(hbreaks)-1))
        # get range from t
        print (sprintf("ts %s ", hbreaks[i] ))
        uh_sub <- uh[which(uh$date > hbreaks[i] & uh$date <= hbreaks[i+1] ),]
        if ( length(uh_sub$uptime ) <= 1 )  { next }

        d<- uh_sub$uptime

        print (sprintf("min: %s, median: %s, max: %s", min(d), median(d), max(d)))

        print (sprintf("length: %s", length(d)))
        q<-quantile(d)
        print(q)

        date_index <- c(date_index, i)

        xx<- c(xx, hbreaks[i])
        q_list <- rbind(q_list, q)

    }
    m<- months[date_index]
    return (cbind(xx,q_list, m))
    # 

}

uh <- read.csv('node_uptime_history.csv', header=TRUE, sep=',')


dm <- uptime_nodes_m3(uh, "2009-06-10", "2010-02-28")

par(mai=c(1,1,0.1,0.1))
    plot(dm[,1], as.numeric(dm[,5])/(60*60*24), type='l', lty=1, xlab="",
            ylim=c(min(as.numeric(dm[,2])/(60*60*24)),max(as.numeric(dm[,5])/(60*60*24))), xlim=c(min(x1[length(x1)/2]), max(x1)), axes=F, ylab="Uptime (days)", col='orange')
    lines(dm[,1], as.numeric(dm[,4])/(60*60*24), lty=1, col='red')
    lines(dm[,1], as.numeric(dm[,3])/(60*60*24), lty=1, col='black')
    lines(dm[,1], as.numeric(dm[,6])/(60*60*24), lty=1, col='orange')
    lines(dm[,1], as.numeric(dm[,2])/(60*60*24), lty=1, col='blue')
    #axis(1, labels=dm[,7], at=dm[,1])
    #axis(2, las=1)
    #m<-round(max(as.numeric(dm[,4])/(60*60*24)), 2)
    #axis(2, labels=m, at=m, las=1)
    #abline(h=m, lty=2, col='grey40')

l<-length(ot[3,])
l2<-l/2
axis(1, labels=ot[3,l2:l], at=ot[1,l2:l], cex.axis=0.7)
axis(2, las=1)
mtext("2007                                    2008                                    2009", 1,2)

tstamp_20041112 <-abline_at_date("2004-11-12", col='grey60', lty=2)
tstamp_20050301 <-abline_at_date("2005-03-01", col='grey60', lty=2)
tstamp_20050615 <-abline_at_date("2005-06-15", col='grey60', lty=2)
tstamp_20051023 <-abline_at_date("2005-10-23", col='grey60', lty=2)
tstamp_20070101 <-abline_at_date("2007-01-01", col='grey60', lty=2)
tstamp_20070501 <-abline_at_date("2007-05-01", col='grey60', lty=2)
tstamp_20080601 <-abline_at_date("2008-06-01", col='grey60', lty=2)
tstamp_20080815 <-abline_at_date("2008-08-15", col='grey60', lty=2)
tstamp_20090501 <-abline_at_date("2009-05-01", col='grey60', lty=2)
tstamp_20100201 <-abline_at_date("2010-02-01", col='white', lty=2)


text(x=c( tstamp_20041112+(tstamp_20050301-tstamp_20041112)/2,
        tstamp_20050301+(tstamp_20050615-tstamp_20050301)/2,
        tstamp_20050615+(tstamp_20051023-tstamp_20050615)/2,
        tstamp_20051023+(tstamp_20070101-tstamp_20051023)/2,
        tstamp_20070101+(tstamp_20070501-tstamp_20070101)/2,
        tstamp_20080601+(tstamp_20080815-tstamp_20080601)/2,
        tstamp_20090501+(tstamp_20100201-tstamp_20090501)/2 ),
     y=c(120),
     labels=c('3.0', '3.1', '3.1S', '3.2', '4.0', '4.2', '4.3')) 

end_image()
