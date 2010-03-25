source("functions.r");


nsh <- read.csv('node_status_history.csv', sep=',', header=TRUE)

# system("./harvest_nodehistory.py > node_status_history_nopcu.csv")
nsh_nopcu <- read.csv('node_status_history_nopcu.csv', sep=',', header=TRUE)

nsh_m1 <- read.csv('node_status_history_m1.csv', sep=',', header=TRUE)
# system("stats-m1/harvest_nodehistory_m1.py > ./node_status_history_m1_nopcu.csv")
nsh_m1_nopcu_total <- read.csv('node_status_history_m1_nopcu_total.csv', sep=',', header=TRUE)
nsh_m1_nopcu_notice <- read.csv('node_status_history_m1_nopcu.csv', sep=',', header=TRUE)
nsh_m1_nopcu_kernel <- read.csv('node_status_history_m1_nopcu_may08sep08.csv', sep=',', header=TRUE)

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



# data collected from M2 pickle files
dnc <- read.csv('daily-available-node-count.csv', sep=',', header=TRUE)

dnc2<-add_timestamp(dnc)

tstamp_08 <-unclass(as.POSIXct("2008-05-07", origin="1970-01-01"))[1]
dnc2 <- dnc2[which( dnc2$start >  tstamp_08 ),]


dates <-seq(as.Date('2008-05-07'), as.Date('2009-05-07'), 'week')
months <- format(dates, "%b")
hbreaks<-unclass(as.POSIXct(dates))

x_start<-unclass(as.POSIXct("2008-05-01", origin="1970-01-01"))[1]
x_end  <-unclass(as.POSIXct("2009-06-1", origin="1970-01-01"))[1]

start_image("myops_restore_nopcu.png")
par(mfrow=c(2,1))
par(mai=c(.9,.8,.1,.1))
plot(dnc2$start[which(!is.na(dnc2$available) & (dnc2$start > tstamp_0815 & dnc2$start <= tstamp_1015) )], 
    dnc2$available[which(!is.na(dnc2$available) & (dnc2$start > tstamp_0815 & dnc2$start <= tstamp_1015) )], 
    type='l', col='red', ylim=c(0,600), xlim=c(x_start, x_end),
    xlab="", ylab="Online Node Count", axes=F)

lines(dnc2$start[which(!is.na(dnc2$available) & (dnc2$start > tstamp_0223) )], 
    dnc2$available[which(!is.na(dnc2$available) & (dnc2$start > tstamp_0223) )], 
    type='l', col='red')

lines(dnc2$start[which(!is.na(dnc2$available) & dnc2$start > tstamp_1015 & dnc2$start <= tstamp_0223)], dnc2$available[which(!is.na(dnc2$available)& dnc2$start > tstamp_1015 & dnc2$start <= tstamp_0223)], lty=2, type='l', col='blue')

lines(dnc2$start[which(!is.na(dnc2$available) & dnc2$start > tstamp_0510 & dnc2$start <= tstamp_0815)], dnc2$available[which(!is.na(dnc2$available)& dnc2$start > tstamp_0510 & dnc2$start <= tstamp_0815)], lty=3, type='l', col='darkgreen')

#lines(dnc2$start[which(!is.na(dnc2$available))], dnc2$available[which(!is.na(dnc2$available))], 
#type='l', col='red', ylim=c(0,1000))
axis(2, las=1)
axis(1, cex.axis=0.7, labels=months, at=hbreaks)
       


#tstamp_0510 <-abline_at_date("2008-05-10", col='grey20', lty=0, height=570)
# dates takes from reboot_image() output for API events.
# green
tstamp_0610 <-abline_at_date("2008-06-10", col='grey40', lty=5, height=570)
tstamp_0815 <-abline_at_date("2008-08-15", col='grey70', lty=1, height=570)

# red
#tstamp_0905 <-abline_at_date("2008-09-05", col='grey70', height=570)
tstamp_0924 <-abline_at_date("2008-09-24", col='grey70', lty=1, height=570)
tstamp_1015 <-abline_at_date("2008-10-15", col='grey40', lty=5, height=570)
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

text(x=c( tstamp_0815,
         tstamp_0924,
         tstamp_0223),
     y=c(610),
     adj=c(1, 0.5),
     labels=c('fix1', 'fix2', 'fix3'))


text(x=c(tstamp_0510-(60*60*24*10), 
        tstamp_0610,
        tstamp_1015),
     adj=c(0, 0.5),
     y=c(610),
     labels=c('Events:', 'bug1', 'bug2'))

mtext("2008                                 2009", 1,2)
legend(unclass(as.POSIXct("2009-02-23", origin="1970-01-01"))[1], 200,
        cex=0.7,
        legend=c("Typical MyOps", "Notice Bug", "Kernel Bug", 'Bug Added', 'Fix Added'),
        pch=c('-', '-', '-'),
        col=c('red', 'blue', 'darkgreen', 'grey20', 'grey70'),
        lty=c(1, 2, 3, 5, 1), merge=T)

        #legend=c("Registered", "Online", 'Kernel Update', 'MyOps Event'),
        #pch=c('-', '-', '-', '-'),
        #col=c('blue', 'red', 'grey20', 'grey70'),
        #lty=c(1, 1, 2, 1), merge=T)

###################################

t_0815 <- unclass(as.POSIXct("2008-08-15", origin="1970-01-01"))[1]
t_0905 <- unclass(as.POSIXct("2008-09-05", origin="1970-01-01"))[1]

t_0924 <- unclass(as.POSIXct("2008-09-24", origin="1970-01-01"))[1]
t_1015 <- unclass(as.POSIXct("2008-10-15", origin="1970-01-01"))[1]

t_0223 <- unclass(as.POSIXct("2009-02-23", origin="1970-01-01"))[1]
t_0313 <- unclass(as.POSIXct("2009-03-13", origin="1970-01-01"))[1]

nsh_m1_short <- nsh_m1_nopcu_total[which( 
        (nsh_m1_nopcu_total$start > t_0815 & nsh_m1_nopcu_total$start <= t_0313) ),]
nsh_dist_m1 <- node_hist_dist(nsh_m1_short, '2008', '2008-05-01', '2009-05-22', 0, 'day')
d_m1_total<- ecdf(nsh_dist_m1/(60*60*24))

# NOTE: something happened betweeen 10-2 and 10-3
# NOTICE BUG
t_1015 <- unclass(as.POSIXct("2008-10-15", origin="1970-01-01"))[1]
t_0224 <- unclass(as.POSIXct("2009-02-24", origin="1970-01-01"))[1]
nsh_m1_short <- nsh_m1_nopcu_notice[which(nsh_m1_nopcu_notice$start > t_1015 & nsh_m1_nopcu_notice$start <= t_0224),]
nsh_dist_m1 <- node_hist_dist(nsh_m1_short, '2008', '2008-10-01', '2009-03-22', 0, 'day')
d_m1_notice_bug <- ecdf(nsh_dist_m1/(60*60*24))


# KERNEL BUG
t_0530 <- unclass(as.POSIXct("2008-05-30", origin="1970-01-01"))[1]
t_0815 <- unclass(as.POSIXct("2008-08-15", origin="1970-01-01"))[1]
nsh_m1_short <- nsh_m1_nopcu_kernel[which(nsh_m1_nopcu_kernel$start > t_0530 & nsh_m1_nopcu_kernel$start <= t_0815),]
nsh_dist_m1 <- node_hist_dist(nsh_m1_short, '2008', '2008-05-10', '2008-08-15', 0, 'day')
d_m1_kernel_bug <- ecdf(nsh_dist_m1/(60*60*24))


# d<-ecdf(nsh_dist[which(nsh_dist/(60*60*24) < 90 )]/(60*60*24)), 
# 180 ~= 6 months.
par(mai=c(.9,.9,.1,.3))
#plot(d, xlim=c(0,180), ylim=c(0,1), axes=F, xlab="Days to Resolve", ylab="Percentile",
#   col.hor='red', col.vert='red', pch='.', col.points='red', main="")

x_lim_max <- 150

plot(d_m1_total, xlim=c(0,x_lim_max), ylim=c(0,1), axes=F, xlab="Days to Resolve", 
    ylab="Fraction of Offline Nodes Restored", col.hor='red', col.vert='red', pch='.', 
    col.points='red', main="")

plot(d_m1_notice_bug, xlim=c(0,x_lim_max), ylim=c(0,1), xlab="Days to Resolve", 
    col.hor='blue', col.vert='blue', pch='.', 
    col.points='blue', lty=2, add=TRUE)

plot(d_m1_kernel_bug, xlim=c(0,x_lim_max), ylim=c(0,1), xlab="Days to Resolve", 
    col.hor='darkgreen', col.vert='darkgreen', pch='.', 
    col.points='darkgreen', lty=3, add=TRUE)

weeks <- c(0,7,14,21,28,60,90,120,150,180)
axis(1, labels=weeks, at=weeks)
percentages <- c(0,0.25, 0.5, 0.75, 0.85, 0.95, 1)
axis(2, las=1, labels=percentages, at=percentages)

abline(v=c(7,14,21,28), col='grey80', lty=2)
abline(h=c(0.5, 0.6, 0.75, 0.85, 0.95 ), col='grey80', lty=2)
abline(v=c(91), col='grey80', lty=2)


legend(92, 0.25,
       cex=0.7,
       legend=c("Typical MyOps", "Notice Bug", "Kernel Bug"),
       pch=c('-', '-', '-'),
       col=c('red', 'blue', 'darkgreen'),
       lty=c(1, 2, 3), merge=T)

end_image()
