"""
Main entry point for NYISO data scraping pipeline.
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from scraper.scraper import NYISOScraper
from scraper.scheduler import NYISOScheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nyiso_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='NYISO Data Scraper')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape data')
    scrape_parser.add_argument('--date', type=str, help='Date to scrape (YYYY-MM-DD)')
    scrape_parser.add_argument('--days', type=int, default=1, help='Number of days to scrape (default: 1)')
    scrape_parser.add_argument('--report-code', type=str, help='Specific report code to scrape')
    scrape_parser.add_argument('--force', action='store_true', help='Force re-scrape')
    
    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Run scheduler')
    schedule_parser.add_argument('--run-once', action='store_true', help='Run scheduled jobs once and exit')
    
    args = parser.parse_args()
    
    if args.command == 'scrape':
        scraper = NYISOScraper()
        try:
            if args.date:
                # Scrape specific date
                date = datetime.strptime(args.date, '%Y-%m-%d')
                job = scraper.scrape_date(date, args.report_code, args.force)
                if job:
                    print(f"Scraping completed: {job.status}")
                    print(f"  Rows inserted: {job.rows_inserted}")
                    print(f"  Rows updated: {job.rows_updated}")
                else:
                    print("Scraping failed")
            else:
                # Scrape recent days
                jobs = scraper.scrape_recent(days=args.days, report_code=args.report_code)
                print(f"Scraped {len(jobs)} jobs")
                for job in jobs:
                    print(f"  {job.data_source.report_code}: {job.status} "
                          f"({job.rows_inserted} inserted, {job.rows_updated} updated)")
        finally:
            scraper.close()
    
    elif args.command == 'schedule':
        scheduler = NYISOScheduler()
        try:
            if args.run_once:
                scheduler.run_once()
            else:
                scheduler.start()
        except KeyboardInterrupt:
            scheduler.stop()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

