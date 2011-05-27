source("functions.r");



median_time_to_resolve_window <- function (t, tg, window)
{
    hbreaks<-tg$week_ts

    xx<-NULL;
    yy<-NULL;
    yy_sd_high<-NULL;
    yy_sd_low<-NULL;
    date_index <- NULL;
    q_list <- NULL;

    x<-seq(-20,20,0.01)

    for ( i in seq(1,length(hbreaks)-window-1) )
    {
        print (sprintf("round %s of %s", i, length(hbreaks)-window-1))
        # get range from t
        t_sub <- t[which(t$start > hbreaks[i] & t$start<= hbreaks[i+window]),]
        if ( length(t_sub$start) <= 1 )  { next }
        # take log, then sn.mle -> h
        d <- (t_sub$lastreply - t_sub$start)/(60*60)    # hours
        d <- log(d)                                     # log(hours)
            # sn.mle
        print (sprintf("length: %s", length(d)))
        q<-quantile(d)
        print(q)

        date_index <- c(date_index, round(i+window/2))

        xx<- c(xx, hbreaks[round(i+window/2)])
        q_list <- rbind(q_list, q)

    }
    return (cbind(xx,q_list))
}

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


open_tickets <- function (t, tg)
{
    xx<-NULL;
    yy<-NULL;

    hbreaks<-tg$day_ts

    for ( i in seq(1,length(hbreaks)-1) )
    {
        # identify any tickets with a start time in range, lastreply in range
        # or where both start is less and lastreply is greater than the range
        t_sub <- t[which( (t$start < hbreaks[i] & t$lastreply > hbreaks[i+1]) | 
                          (t$start > hbreaks[i] & t$start <= hbreaks[i+1]) | 
                          (t$lastreply > hbreaks[i] & t$lastreply <= hbreaks[i+1]) ),]
        tickets <- length(t_sub$start)

        xx<- c(xx, hbreaks[i])
        yy<- c(yy, tickets)
    }
    return (rbind(xx,yy))
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

#####

# system("rt_s1_raw_dump.py --runsql");
# system("rt_s2_parse_raw.py 3 > rt_data.csv");
# t <- read.csv('rt_data_2004-2011.csv', sep=',', header=TRUE)
#t <- read.csv(, sep=',', header=TRUE)

draw_rt_data <- function (input_filename, output_filename, start_date, end_date, draw=TRUE, one=FALSE)
{
    t <- read.csv(input_filename, sep=',', header=TRUE)
    t2 <- t[which(t$complete == 1),]

    tg <- time_graph_setup(start_date, end_date) 
    ot <- open_tickets(t2, tg)

    if ( draw == TRUE ) {
        start_image(output_filename, width=600, height=400)
    }
    if ( one == TRUE )
    {
        par(mfrow=c(1,1))
        par(mai=c(0.8,1,0.4,0.1))
    } else {
        par(mfrow=c(2,1))
        par(mai=c(0,1,0.3,0.1))
    }

    x1<-as.numeric(ot[1,])
    y1<-as.numeric(ot[2,])

    a_ot<-lowess_smooth(x1, y1)

    plot(x1, y1, col='grey80', type='l', axes=F, 
        ylab="a) Open Tickets (tickets/day)", xlab="Date",
        ylim=c(0,120)) # , ylim=c(0,260))
    lines(a_ot$x, round(a_ot$y), col='black')

    axis(2, las=1)
    if ( one == TRUE ) {
        axis(1, labels=tg$month_str, at=tg$month_ts, cex.axis=0.7)
        axis(1, labels=tg$year_str, at=tg$year_ts, cex.axis=0.7, line=1, lwd=0)
    }


    abline(h=15, lty=3, col='grey80')
    abline(h=25, lty=3, col='grey80')
    abline(h=40, lty=3, col='grey80')

    plc_releases(120)
    if ( one == FALSE )
    {
        par(mai=c(1,1,0.1,0.1))
        for ( s in c(5) ) 
        {
            d <- median_time_to_resolve_window(t2, tg, s) # "2004/1/1", "2011/1/28", s, "%b")
            plot(d[,1], exp(as.numeric(d[,5]))/24, type='l', lty=1, xlab="",
                    axes=F, ylim=c(0.01, 15), ylab="b) Resolution Time by", col='black',
                    xlim=c(min(x1), max(x1)))
            mtext("Quartile (days)", 2, 2)
            lines(d[,1], exp(as.numeric(d[,4]))/24, lty=1, col='grey50')
            lines(d[,1], exp(as.numeric(d[,3]))/24, lty=1, col='grey75')
            axis(1, labels=tg$month_str, at=tg$month_ts, cex.axis=0.7)
            axis(1, labels=tg$year_str, at=tg$year_ts, cex.axis=0.7, line=1, lwd=0)
            axis(2, labels=c(0,1,4,7,14), at=c(0,1,4,7,14), las=1)
            m<-round(max(exp(as.numeric(d[,4]))/24), 2)
        }

        abline(h=1, lty=3, col='grey80')
        abline(h=4, lty=3, col='grey80')
        abline(h=7, lty=3, col='grey80')

        planetlab_releases(15)
    }

    if ( draw == TRUE ) {
        end_image()
    }
}

#system("./rt_s2_parse_raw.py 3 > rt_data_2004-2011.csv");
draw_rt_data('rt_data_2004-2011.csv', "rt_operator_support_2004-2011.png", "2004/1/1", "2011/6/1", TRUE, TRUE)
#draw_rt_data('rt_data_monitor_2004-2011.csv',"rt_operator_monitor_2004-2011.png", "2004/1/1", "2011/4/1")

#draw_rt_data('short_support_20110101.csv',"rt_short_2011.png", "2010/11/1", "2011/4/1", FALSE)
