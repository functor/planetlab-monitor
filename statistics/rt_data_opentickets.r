source("functions.r");

# system("parse_rt_data.py 3 > rt_data.csv");
t <- read.csv('rt_data_2004-2010.csv', sep=',', header=TRUE)
t2 <- t[which(t$complete == 1),]


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
        # get range from t
        t_sub <- t[which(t$start > hbreaks[i] & t$lastreply <= hbreaks[i+1]),]
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

ot <- open_tickets(t2, '2004/1/1', '2010/2/28', 'week', "%b%y")

plot(ot[1,], ot[2,], axes=F)
y<- ot[2,]
s<-which(y!='0')
y<-y[s]
y<-as.numeric(y)
plot(ot[1,s],y)
axis(1, labels=ot[3,], at=ot[1,])
axis(2)

ot <- open_tickets(t2, '2004/1/1', '2010/2/28', 'day', "%b%y")
x1<-as.numeric(ot[1,])
y1<-as.numeric(ot[2,])

# remove zero
#s<-which(y1!='0')
#y1<-y1[s]
#x1<-x1[s]

y1<-as.numeric(y1)

lines(x1, y1, axes=F, pch='.')
axis(1, labels=ot[3,], at=ot[1,])
axis(2)
#lines(ot[1,], ot[2,])
#a<-smooth(as.numeric(y1))
#x<-x1
#y<-a

a<-lowess(x1, y1, delta=(60*60*24), f=0.03)
x<-a$x
y<-a$y

#y<-rollmedian(y1, 5)
#x<-x1[1:length(y)]

lines(x, y, col='red')
lines(x, round(y), col='blue')
#lines(x, ceiling(y), col='blue')

abline_at_date('2005-01-01', 'grey40')
abline_at_date('2006-01-01', 'grey40')
abline_at_date('2007-01-01', 'grey40')
abline_at_date('2008-01-01', 'grey40')
abline_at_date('2009-01-01', 'grey40')
abline_at_date('2010-01-01', 'grey40')

