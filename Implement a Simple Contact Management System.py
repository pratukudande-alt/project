import json
import os
import re
from datetime import datetime
from typing import List, Optional, Dict
import sys

class Contact:
    """Represents a single contact with validation"""
    
    def __init__(self, name: str, phone: str, email: str, contact_id: Optional[str] = None):
        self.name = name.strip()
        self.phone = self._validate_phone(phone)
        self.email = self._validate_email(email)
        self.contact_id = contact_id or self._generate_id()
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    @staticmethod
    def _validate_phone(phone: str) -> str:
        """Validate and format phone number"""
        # Remove any non-digit characters
        cleaned = re.sub(r'\D', '', phone)
        if len(cleaned) < 7:
            raise ValueError("Phone number must have at least 7 digits")
        return cleaned
    
    @staticmethod
    def _validate_email(email: str) -> str:
        """Validate email format"""
        email = email.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique contact ID"""
        return f"CONT_{int(datetime.now().timestamp())}_{os.urandom(4).hex().upper()}"
    
    def update(self, name: Optional[str] = None, phone: Optional[str] = None, 
               email: Optional[str] = None) -> bool:
        """Update contact fields"""
        updated = False
        
        if name and name.strip():
            self.name = name.strip()
            updated = True
        
        if phone:
            try:
                self.phone = self._validate_phone(phone)
                updated = True
            except ValueError:
                raise
        
        if email:
            try:
                self.email = self._validate_email(email)
                updated = True
            except ValueError:
                raise
        
        if updated:
            self.updated_at = datetime.now().isoformat()
        
        return updated
    
    def to_dict(self) -> Dict:
        """Convert contact to dictionary for JSON serialization"""
        return {
            'id': self.contact_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Contact':
        """Create Contact object from dictionary"""
        contact = cls(
            name=data['name'],
            phone=data['phone'],
            email=data['email'],
            contact_id=data['id']
        )
        contact.created_at = data.get('created_at', datetime.now().isoformat())
        contact.updated_at = data.get('updated_at', datetime.now().isoformat())
        return contact
    
    def get_formatted_phone(self) -> str:
        """Return formatted phone number"""
        phone = self.phone
        if len(phone) == 10:
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        elif len(phone) == 11:
            return f"{phone[0]}-({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
        return phone
    
    def __str__(self) -> str:
        return f"📱 {self.name}\n   📞 {self.get_formatted_phone()}\n   ✉️  {self.email}"

class ContactManager:
    """Manages a collection of contacts with persistence"""
    
    def __init__(self, filename: str = 'contacts.json'):
        self.filename = filename
        self.contacts: List[Contact] = []
        self.load_contacts()
    
    def load_contacts(self) -> None:
        """Load contacts from JSON file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.contacts = [Contact.from_dict(contact) for contact in data]
                print(f"✅ Loaded {len(self.contacts)} contacts from {self.filename}")
            except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                print(f"⚠️  Error loading contacts: {e}. Starting with empty list.")
                self.contacts = []
        else:
            print(f"📁 No existing contacts file found. Starting fresh.")
            self.contacts = []
    
    def save_contacts(self) -> bool:
        """Save contacts to JSON file"""
        try:
            # Create backup if file exists
            if os.path.exists(self.filename):
                backup_name = f"{self.filename}.backup"
                try:
                    os.rename(self.filename, backup_name)
                except:
                    pass
            
            with open(self.filename, 'w', encoding='utf-8') as file:
                json.dump([contact.to_dict() for contact in self.contacts], 
                         file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving contacts: {e}")
            return False
    
    def add_contact(self, name: str, phone: str, email: str) -> bool:
        """Add a new contact"""
        try:
            # Check for duplicate name (case-insensitive)
            if any(c.name.lower() == name.strip().lower() for c in self.contacts):
                print(f"⚠️  A contact with name '{name}' already exists.")
                return False
            
            # Check for duplicate phone
            clean_phone = re.sub(r'\D', '', phone)
            if any(c.phone == clean_phone for c in self.contacts):
                print(f"⚠️  Phone number already exists for another contact.")
                return False
            
            # Check for duplicate email
            clean_email = email.strip().lower()
            if any(c.email == clean_email for c in self.contacts):
                print(f"⚠️  Email already exists for another contact.")
                return False
            
            contact = Contact(name, phone, email)
            self.contacts.append(contact)
            self.save_contacts()
            print(f"✅ Contact '{name}' added successfully!")
            return True
            
        except ValueError as e:
            print(f"❌ Error: {e}")
            return False
    
    def find_contact_by_id(self, contact_id: str) -> Optional[Contact]:
        """Find contact by ID"""
        for contact in self.contacts:
            if contact.contact_id == contact_id:
                return contact
        return None
    
    def find_contact_by_name(self, name: str, exact: bool = False) -> List[Contact]:
        """Find contacts by name"""
        name_lower = name.strip().lower()
        if exact:
            contacts = [c for c in self.contacts if c.name.lower() == name_lower]
        else:
            contacts = [c for c in self.contacts if name_lower in c.name.lower()]
        return contacts
    
    def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts by name, phone, or email"""
        query_lower = query.strip().lower()
        results = []
        
        for contact in self.contacts:
            if (query_lower in contact.name.lower() or
                query_lower in contact.phone or
                query_lower in contact.email.lower()):
                results.append(contact)
        
        return results
    
    def edit_contact(self, identifier: str, name: Optional[str] = None, 
                     phone: Optional[str] = None, email: Optional[str] = None) -> bool:
        """Edit an existing contact"""
        # Try to find by ID first, then by name
        contact = self.find_contact_by_id(identifier)
        if not contact:
            matches = self.find_contact_by_name(identifier)
            if not matches:
                print(f"❌ Contact '{identifier}' not found.")
                return False
            if len(matches) > 1:
                print(f"⚠️  Multiple contacts found. Please be more specific:")
                for c in matches:
                    print(f"   - {c.name} ({c.contact_id})")
                return False
            contact = matches[0]
        
        try:
            if contact.update(name, phone, email):
                self.save_contacts()
                print(f"✅ Contact updated successfully!")
                return True
            else:
                print("ℹ️  No changes were made.")
                return False
        except ValueError as e:
            print(f"❌ Error: {e}")
            return False
    
    def delete_contact(self, identifier: str) -> bool:
        """Delete a contact"""
        # Try to find by ID first, then by name
        contact = self.find_contact_by_id(identifier)
        if not contact:
            matches = self.find_contact_by_name(identifier)
            if not matches:
                print(f"❌ Contact '{identifier}' not found.")
                return False
            if len(matches) > 1:
                print(f"⚠️  Multiple contacts found. Please be more specific:")
                for c in matches:
                    print(f"   - {c.name} ({c.contact_id})")
                return False
            contact = matches[0]
        
        print(f"\n📋 Contact to delete:")
        print(contact)
        
        confirm = input(f"\nAre you sure you want to delete '{contact.name}'? (y/n): ").lower()
        if confirm == 'y':
            self.contacts.remove(contact)
            self.save_contacts()
            print(f"✅ Contact '{contact.name}' deleted successfully!")
            return True
        else:
            print("❌ Deletion cancelled.")
            return False
    
    def get_all_contacts(self, sort_by: str = 'name') -> List[Contact]:
        """Get all contacts sorted by specified field"""
        if sort_by == 'name':
            return sorted(self.contacts, key=lambda c: c.name.lower())
        elif sort_by == 'created':
            return sorted(self.contacts, key=lambda c: c.created_at)
        elif sort_by == 'updated':
            return sorted(self.contacts, key=lambda c: c.updated_at, reverse=True)
        return self.contacts
    
    def get_statistics(self) -> Dict:
        """Get contact statistics"""
        total = len(self.contacts)
        if total == 0:
            return {'total': 0}
        
        name_lengths = [len(c.name) for c in self.contacts]
        phone_types = {'mobile': 0, 'landline': 0, 'other': 0}
        for c in self.contacts:
            if len(c.phone) == 10:
                phone_types['mobile'] += 1
            elif len(c.phone) == 11:
                phone_types['landline'] += 1
            else:
                phone_types['other'] += 1
        
        return {
            'total': total,
            'avg_name_length': sum(name_lengths) / total,
            'phone_types': phone_types
        }

class ContactApp:
    """Main application class with user interface"""
    
    def __init__(self):
        self.manager = ContactManager()
    
    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("📇 CONTACT MANAGEMENT SYSTEM")
        print("="*60)
        print("1.  ➕ Add New Contact")
        print("2.  📋 View All Contacts")
        print("3.  🔍 Search Contacts")
        print("4.  ✏️  Edit Contact")
        print("5.  🗑️  Delete Contact")
        print("6.  📊 View Statistics")
        print("7.  💾 Backup Contacts")
        print("8.  🔄 Restore from Backup")
        print("9.  ❌ Exit")
        print("="*60)
    
    def add_contact_ui(self):
        """UI for adding a contact"""
        print("\n--- ➕ ADD NEW CONTACT ---")
        
        name = input("Enter name: ").strip()
        if not name:
            print("❌ Name cannot be empty.")
            return
        
        phone = input("Enter phone number: ").strip()
        if not phone:
            print("❌ Phone number cannot be empty.")
            return
        
        email = input("Enter email address: ").strip()
        if not email:
            print("❌ Email cannot be empty.")
            return
        
        self.manager.add_contact(name, phone, email)
    
    def view_contacts_ui(self):
        """UI for viewing all contacts"""
        contacts = self.manager.get_all_contacts()
        
        if not contacts:
            print("\n📭 No contacts found.")
            return
        
        print(f"\n{'='*60}")
        print(f"📋 CONTACT LIST ({len(contacts)} contacts)")
        print(f"{'='*60}")
        
        for i, contact in enumerate(contacts, 1):
            print(f"\n{i}. {contact}")
            print(f"   🆔 ID: {contact.contact_id}")
            print(f"   📅 Created: {contact.created_at[:16]}")
            print(f"   📅 Updated: {contact.updated_at[:16]}")
            print("-" * 50)
    
    def search_contacts_ui(self):
        """UI for searching contacts"""
        print("\n--- 🔍 SEARCH CONTACTS ---")
        print("Search by name, phone, or email")
        query = input("Enter search term: ").strip()
        
        if not query:
            print("❌ Search term cannot be empty.")
            return
        
        results = self.manager.search_contacts(query)
        
        if not results:
            print(f"\n🔍 No contacts found matching '{query}'.")
            return
        
        print(f"\n{'='*60}")
        print(f"🔍 SEARCH RESULTS ({len(results)} contacts found)")
        print(f"{'='*60}")
        
        for i, contact in enumerate(results, 1):
            print(f"\n{i}. {contact}")
            print(f"   🆔 ID: {contact.contact_id}")
            print("-" * 50)
    
    def edit_contact_ui(self):
        """UI for editing a contact"""
        print("\n--- ✏️  EDIT CONTACT ---")
        
        # Show all contacts first
        self.view_contacts_ui()
        print()
        
        identifier = input("Enter contact name or ID to edit: ").strip()
        if not identifier:
            print("❌ Identifier cannot be empty.")
            return
        
        contact = self.manager.find_contact_by_id(identifier)
        if not contact:
            matches = self.manager.find_contact_by_name(identifier)
            if not matches:
                print(f"❌ Contact '{identifier}' not found.")
                return
            if len(matches) > 1:
                print("⚠️  Multiple contacts found. Please use the ID for precise selection.")
                for c in matches:
                    print(f"   - {c.name} (ID: {c.contact_id})")
                return
            contact = matches[0]
        
        print(f"\n📋 Current Contact Details:")
        print(contact)
        print("\nLeave field blank to keep current value")
        
        new_name = input(f"\nNew name [{contact.name}]: ").strip()
        new_phone = input(f"New phone [{contact.get_formatted_phone()}]: ").strip()
        new_email = input(f"New email [{contact.email}]: ").strip()
        
        self.manager.edit_contact(
            contact.contact_id,
            name=new_name if new_name else None,
            phone=new_phone if new_phone else None,
            email=new_email if new_email else None
        )
    
    def delete_contact_ui(self):
        """UI for deleting a contact"""
        print("\n--- 🗑️  DELETE CONTACT ---")
        
        # Show all contacts first
        self.view_contacts_ui()
        print()
        
        identifier = input("Enter contact name or ID to delete: ").strip()
        if not identifier:
            print("❌ Identifier cannot be empty.")
            return
        
        self.manager.delete_contact(identifier)
    
    def view_statistics_ui(self):
        """UI for viewing statistics"""
        stats = self.manager.get_statistics()
        
        print("\n" + "="*60)
        print("📊 CONTACT STATISTICS")
        print("="*60)
        print(f"Total Contacts: {stats['total']}")
        
        if stats['total'] > 0:
            print(f"Average Name Length: {stats['avg_name_length']:.1f} characters")
            print("\nPhone Number Types:")
            print(f"  Mobile (10 digits): {stats['phone_types']['mobile']}")
            print(f"  Landline (11 digits): {stats['phone_types']['landline']}")
            print(f"  Other: {stats['phone_types']['other']}")
        
        print("="*60)
    
    def backup_contacts_ui(self):
        """UI for backing up contacts"""
        if not self.manager.contacts:
            print("📭 No contacts to backup.")
            return
        
        backup_name = f"contacts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            # Save a copy
            with open(backup_name, 'w', encoding='utf-8') as file:
                json.dump([contact.to_dict() for contact in self.manager.contacts], 
                         file, indent=2, ensure_ascii=False)
            print(f"✅ Backup saved as: {backup_name}")
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
    
    def restore_from_backup_ui(self):
        """UI for restoring from backup"""
        # Find backup files
        backup_files = [f for f in os.listdir('.') if f.startswith('contacts_backup_') and f.endswith('.json')]
        
        if not backup_files:
            print("📭 No backup files found.")
            return
        
        print("\n📂 Available Backups:")
        for i, file in enumerate(backup_files, 1):
            print(f"  {i}. {file}")
        
        try:
            choice = int(input("\nSelect backup to restore (number): ")) - 1
            if 0 <= choice < len(backup_files):
                backup_file = backup_files[choice]
                
                with open(backup_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    restored_contacts = [Contact.from_dict(c) for c in data]
                
                confirm = input(f"⚠️  This will replace all current contacts with {len(restored_contacts)} contacts from backup. Continue? (y/n): ").lower()
                if confirm == 'y':
                    self.manager.contacts = restored_contacts
                    self.manager.save_contacts()
                    print(f"✅ Restored {len(restored_contacts)} contacts from backup.")
                else:
                    print("❌ Restore cancelled.")
            else:
                print("❌ Invalid selection.")
        except (ValueError, IndexError):
            print("❌ Invalid input.")
    
    def run(self):
        """Main application loop"""
        print("\n" + "="*60)
        print("📇 WELCOME TO CONTACT MANAGEMENT SYSTEM")
        print("="*60)
        
        while True:
            self.display_menu()
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == '1':
                self.add_contact_ui()
            elif choice == '2':
                self.view_contacts_ui()
            elif choice == '3':
                self.search_contacts_ui()
            elif choice == '4':
                self.edit_contact_ui()
            elif choice == '5':
                self.delete_contact_ui()
            elif choice == '6':
                self.view_statistics_ui()
            elif choice == '7':
                self.backup_contacts_ui()
            elif choice == '8':
                self.restore_from_backup_ui()
            elif choice == '9':
                print("\n✅ Contacts saved. Goodbye! 👋")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter a number between 1 and 9.")
            
            input("\nPress Enter to continue...")

def main():
    """Entry point for the application"""
    try:
        app = ContactApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted. Goodbye! 👋")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()