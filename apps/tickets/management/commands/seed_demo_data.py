from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.tickets.models import Ticket, TicketMessage

User = get_user_model()

CUSTOMERS = [
    ("leo_messi", "Leo", "Messi", "pass_leo"),
    ("cristiano_ronaldo", "Cristiano", "Ronaldo", "pass_cristiano"),
    ("kylian_mbappe", "Kylian", "Mbappe", "pass_kylian"),
    ("mohamed_salah", "Mohamed", "Salah", "pass_mohamed"),
    ("kevin_debruyne", "Kevin", "De Bruyne", "pass_kevin"),
    ("erling_haaland", "Erling", "Haaland", "pass_erling"),
]

AGENTS = [
    ("amelia_rossi", "Amelia", "Rossi", "pass_amelia"),
    ("michael_chen", "Michael", "Chen", "pass_michael"),
    ("lucas_meyer", "Lucas", "Meyer", "pass_lucas"),
    ("nadia_ibrahim", "Nadia", "Ibrahim", "pass_nadia"),
]

#DEMO_USERNAMES = [u[0] for u in CUSTOMERS + AGENTS]

DEMO_USERNAMES = []
for u in CUSTOMERS + AGENTS:
    DEMO_USERNAMES.append(u[0])


class Command(BaseCommand):
    help = "Seed the database with demo users, tickets, and messages."

    def handle(self, *args, **options):
        self.stdout.write("Clearing previous demo data...")
        self._clear_demo_data()

        self.stdout.write("Creating demo users...")
        customers = {u[0]: self._create_user(*u, role="CUSTOMER") 
                     for u in CUSTOMERS
        }
        agents = {u[0]: self._create_user(*u, role="AGENT") 
                  for u in AGENTS
        }

        self.stdout.write("Creating demo tickets...")
        self._create_tickets(customers, agents)

        total = Ticket.objects.filter(created_by__username__in=DEMO_USERNAMES).count()
        self.stdout.write(self.style.SUCCESS(
            f"Done. Seeded {len(customers)} customers, {len(agents)} agents, {total} tickets."
        ))

    def _clear_demo_data(self):
        old_tickets = Ticket.objects.filter(created_by__username__in=DEMO_USERNAMES)
        TicketMessage.objects.filter(ticket__in=old_tickets).delete()
        old_tickets.delete()
        User.objects.filter(username__in=DEMO_USERNAMES).delete()

    def _create_user(self, username, first_name, last_name, password, role):
        return User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=f"{username}@example.com",
            password=password,
            role=role,
        )

    def _create_tickets(self, customers, agents):
        now = timezone.now()

        def make_ticket(customer_username, title, description, status, priority,
                         assigned_username=None, message_count=0, author_cycle=None):
            ticket = Ticket.objects.create(
                title=title,
                description=description,
                created_by=customers[customer_username],
                status=status,
                priority=priority,
                assigned_to=agents[assigned_username] if assigned_username else None,
            )
            if message_count:
                authors = author_cycle or [customer_username, assigned_username]
                for i in range(message_count):
                    author_username = authors[i % len(authors)]
                    author = customers.get(author_username) or agents.get(author_username)
                    TicketMessage.objects.create(
                        ticket=ticket,
                        author=author,
                        text=f"Message {i + 1} on '{title}' from {author.first_name}.",
                        created_at=now - timedelta(hours=message_count - i),
                    )
            return ticket

        make_ticket("leo_messi", "Cannot log into my account",
                    "I keep getting 'invalid credentials' even after resetting my password.",
                    "open", "medium")

        make_ticket("cristiano_ronaldo", "App crashes on file upload",
                    "Every time I try to upload a profile photo the app closes immediately.",
                    "open", "high")

        make_ticket("kylian_mbappe", "Payment failed but I was still charged",
                    "My card was charged twice for the same subscription renewal.",
                    "in_progress", "urgent", "amelia_rossi", message_count=3,
                    author_cycle=["kylian_mbappe", "amelia_rossi"])

        make_ticket("mohamed_salah", "Minor UI glitch on settings page",
                    "The save button overlaps with the cancel button on mobile view.",
                    "in_progress", "low", "amelia_rossi", message_count=2,
                    author_cycle=["mohamed_salah", "amelia_rossi"])

        make_ticket("kevin_debruyne", "Two-factor codes never arrive",
                    "SMS codes for 2FA login have not arrived for the past three attempts.",
                    "in_progress", "medium", "michael_chen", message_count=4,
                    author_cycle=["kevin_debruyne", "michael_chen"])

        make_ticket("erling_haaland", "Export to CSV missing rows",
                    "Exported reports are missing the last 10 rows of data consistently.",
                    "resolved", "high", "michael_chen", message_count=3,
                    author_cycle=["erling_haaland", "michael_chen"])

        make_ticket("leo_messi", "Notification settings not saving",
                    "I turn off email notifications but they turn back on after a day.",
                    "in_progress", "urgent", "lucas_meyer", message_count=2,
                    author_cycle=["leo_messi", "lucas_meyer"])

        make_ticket("cristiano_ronaldo", "Requesting account data export",
                    "Please send a full export of my account data for my records.",
                    "closed", "medium", "lucas_meyer", message_count=3,
                    author_cycle=["cristiano_ronaldo", "lucas_meyer"])

        make_ticket("kylian_mbappe", "Dark mode toggle missing on tablet",
                    "The dark mode switch shown on desktop does not appear on my tablet app.",
                    "open", "low")

        make_ticket("mohamed_salah", "Unable to cancel subscription",
                    "The cancel subscription button does nothing when clicked.",
                    "open", "high")

        make_ticket("kevin_debruyne", "Wrong billing address on invoice",
                    "My last invoice shows an old billing address I removed months ago.",
                    "in_progress", "medium", "nadia_ibrahim", message_count=2,
                    author_cycle=["kevin_debruyne", "nadia_ibrahim"])

        make_ticket("erling_haaland", "Feature request: bulk delete",
                    "It would help a lot to select and delete multiple tickets at once.",
                    "open", "urgent")    