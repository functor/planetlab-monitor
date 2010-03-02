source("functions.r");

nsh <- read.csv('node_status_history.csv', sep=',', header=TRUE)

# system("./harvest_nodehistory.py > node_status_history_nopcu.csv")
nsh_nopcu <- read.csv('node_status_history_nopcu.csv', sep=',', header=TRUE)

nsh_m1 <- read.csv('node_status_history_m1.csv', sep=',', header=TRUE)
# system("stats-m1/harvest_nodehistory_m1.py > ./node_status_history_m1_nopcu.csv")
nsh_m1_nopcu <- read.csv('node_status_history_m1_nopcu.csv', sep=',', header=TRUE)
nsh_m1_nopcu_may <- read.csv('node_status_history_m1_nopcu_may08sep08.csv', sep=',', header=TRUE)

node_hist_image <- function (t, year, from, to, max=0, type="week", title="")
{
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, "%b-%d")
    hbreaks<-unclass(as.POSIXct(dates))

    image <- matrix(data=0, nrow=max(as.numeric(t$hostname)), ncol=length(hbreaks))

    for ( i in seq(1, length(hbreaks)) )
    {
        # find the range : d plus a day
        d <- hbreaks[i]
        d_end <- d+60*60*24
        # find unique hosts in this day range
        t_sub <- t[which(t$start > d & t$start <= d_end & t$status == 'down'),]
        unique_hosts <- unique(t_sub$hostname)
        if (length(unique_hosts) == 0 ) { next }

        host_n_list <- unique_hosts
        host_s_list <- as.character(unique_hosts)

        for ( hi in seq(1, length(unique_hosts))  ) 
        {
            host_s <- host_s_list[hi]
            host_n <- host_n_list[hi]
            # events for this host after d (to avoid already identified events)
            ev <- t[which(t$hostname == host_s & t$start > d ),]
            print (sprintf("events length for host %s %s", host_s, length(ev$start)));
            # get down events for this host
            down_ev_index_list <- which(ev$status == 'down')
            for ( e_i in down_ev_index_list )
            {
                if ( e_i == length(ev$status) ) { 
                    # then the node ends down, so fill in the rest with 1.
                    for ( j in seq(i,length(hbreaks)) ) {
                        image[host_n,j] <- 1
                    }
                } else {
                    # then there is a subsequent 'good' event
                    good_ev <- ev[e_i+1,]
                    down_ev <- ev[e_i,]
                    dbreaks <- seq(d,good_ev$start+60*60*24,60*60*24)
                    # for every index for time d, to good_ev$start
                    l<-length(dbreaks)
                    print (sprintf("length %s",l));
                    for ( j in seq(i,i+l) )
                    {
                        image[host_n,j] <- 1
                    }
                }
            }
        }
    }
    myImagePlot(image, xLabels=months, yLabels=c(""), title=title)
    return (image);
}



node_hist_dist <- function (t, year, from, to, max=0, type="week", title="")
{
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, "%b-%d")
    hbreaks<-unclass(as.POSIXct(dates))
    current_ts <- unclass(as.POSIXct(Sys.Date()))

    dist <- NULL

    unique_hosts <- unique(t$hostname)
    host_n_list <- unique_hosts
    host_s_list <- as.character(unique_hosts)

    down <- 0

    for ( hi in seq(1, length(unique_hosts))  ) 
    {
        host_s <- host_s_list[hi]
        host_n <- host_n_list[hi]
        # events for this host after d (to avoid already identified events)
        ev <- t[which( t$hostname == host_s ),]
        print (sprintf("events length for host %s %s", host_s, length(ev$start)));
        # get down events for this host
        down_ev_index_list <- which(ev$status == 'down')
        for ( e_i in down_ev_index_list )
        {
            # when equal, there is no resolution so leave it as down
            if ( e_i != length(ev$status) ) { 
                good_ev <- ev[e_i+1,]
                down_ev <- ev[e_i,]
                dist <- c(dist, good_ev$start - down_ev$start)
            } else if ( e_i == length(ev$status) && length(ev$status) == 1) { 
                print (sprintf("DOWN FOREVER! %s", length(ev$start) ))
                down <- down + 1
                dist <- c(dist, 10*current_ts - ev$start)
            }
        }
    }
    print(down);
    return (dist);
}

nsh_image <- node_hist_image(nsh, '2009', '2009-06-01', '2010-02-28', 0, 'day')
nsh_image_m1 <- node_hist_image(nsh_m1, '2009', '2008-10-01', '2009-03-28', 0, 'day')


nsh_short <- nsh[which(nsh$start > unclass(as.POSIXct("2009-06-01", origin="1970-01-01"))[1]),]
nsh_short <- nsh_short[which(nsh_short$start < unclass(as.POSIXct("2009-10-31", origin="1970-01-01"))[1]),]


nsh_short <- nsh_nopcu
nsh_dist <- node_hist_dist(nsh_short, '2009', '2009-06-01', '2010-02-28', 0, 'day')
d<- ecdf(nsh_dist/(60*60*24))

#nsh_m1_short <- nsh_m1[which(nsh_m1$start > unclass(as.POSIXct("2008-10-01", origin="1970-01-01"))[1]),]
nsh_m1_short <- nsh_m1_nopcu
# NOTE: something happened betweeen 10-2 and 10-3
t_1015 <- unclass(as.POSIXct("2008-10-15", origin="1970-01-01"))[1]
t_0224 <- unclass(as.POSIXct("2009-02-24", origin="1970-01-01"))[1]
nsh_m1_short <- nsh_m1_nopcu[which(nsh_m1_nopcu$start > t_1015 & nsh_m1_nopcu$start <= t_0224),]

nsh_m1_short <- nsh_m1_nopcu
nsh_dist_m1 <- node_hist_dist(nsh_m1_short, '2008', '2008-10-01', '2009-03-22', 0, 'day')
d_m1<- ecdf(nsh_dist_m1/(60*60*24))


t_0530 <- unclass(as.POSIXct("2008-05-30", origin="1970-01-01"))[1]
t_0815 <- unclass(as.POSIXct("2008-08-15", origin="1970-01-01"))[1]
nsh_m1_short <- nsh_m1_nopcu_may[which(nsh_m1_nopcu_may$start > t_0530 & nsh_m1_nopcu_may$start <= t_0815),]
nsh_dist_m1 <- node_hist_dist(nsh_m1_short, '2008', '2008-05-10', '2008-08-15', 0, 'day')
d_m1_may <- ecdf(nsh_dist_m1/(60*60*24))


# d<-ecdf(nsh_dist[which(nsh_dist/(60*60*24) < 90 )]/(60*60*24)), 
# 180 ~= 6 months.
par(mfrow=c(1,1))
par(mai=c(.9,.9,.1,.1))
start_image("node_history_ttr_nopcu.png")
plot(d, xlim=c(0,180), ylim=c(0,1), axes=F, xlab="Days to Resolve", ylab="Percentile",
   col.hor='red', col.vert='red', pch='.', col.points='red', main="")
plot(d_m1, xlim=c(0,180), ylim=c(0,1), xlab="Days to Resolve", ylab="Percentile",
   col.hor='blue', col.vert='blue', pch='.', col.points='blue', add=TRUE)
plot(d_m1_may, xlim=c(0,180), ylim=c(0,1), xlab="Days to Resolve", ylab="Percentile",
   col.hor='green', col.vert='green', pch='.', col.points='green', add=TRUE)

weeks <- c(0,7,14,21,28,60,90,120,150,180)
axis(1, labels=weeks, at=weeks)
percentages <- c(0,0.25, 0.5, 0.75, 0.85, 0.95, 1)
axis(2, las=1, labels=percentages, at=percentages)

abline(v=c(7,14,21,28), col='grey80', lty=2)
abline(h=c(0.5, 0.6, 0.75, 0.85, 0.95 ), col='grey80', lty=2)
abline(v=c(91), col='grey80', lty=2)


legend(100, 0.1,
       cex=0.7,
       legend=c("Typical MyOps -- July2009-Feb2010", "Notice Bug -- Oct2008-Mar2009", "Kernel Bug -- May2008-Sept2008"),
       pch=c('-', '-', '-'),
       col=c('red', 'blue', 'green'),
       lty=c(1, 1, 1), merge=T)
end_image()
