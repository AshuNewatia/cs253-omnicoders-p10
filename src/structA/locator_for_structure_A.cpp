#include <algorithm>
#include <stdexcept>
#include <string>
#include <vector>

int CAP = 1024;

struct twin {
    int ID;
    int address;
    twin(int id, int index = -1) : ID(id), address(index) {}
};

twin e(-1, -1);

class LookUp {
private:
    std::vector<twin> tab;
    int state_count = 0;
    // Includes deleted slots: this is the actual probe-table occupancy.
    int used_count = 0;

    long long hashie(int input) const {
        const std::string input_str = std::to_string(input);
        long long hash = 0;
        for (char ch : input_str) hash = hash * 31 + static_cast<unsigned char>(ch);
        return hash;
    }

    int find_slot(int id) const {
        const int start = static_cast<int>(hashie(id) % CAP);
        for (int offset = 0; offset < CAP; ++offset) {
            const int slot = (start + offset) % CAP;
            if (tab[slot].ID == id) return slot;
            if (tab[slot].ID == -1) return -1;
        }
        return -1;
    }

    void resize(int new_capacity) {
        const std::vector<twin> old_tab = tab;
        CAP = new_capacity;
        tab.assign(CAP, e);
        state_count = 0;
        used_count = 0;
        for (const twin& entry : old_tab) {
            if (entry.ID != -1 && entry.ID != -2) Insert(entry);
        }
    }

public:
    LookUp() : tab(CAP, e) {}
    int find(int id) const {
        const int slot = find_slot(id);
        if (slot == -1) throw std::out_of_range("Not Found");
        return tab[slot].address;
    }

    void Insert(twin in) {
        // If tombstones caused the table to fill, rehash at the same size;
        // grow only when the live set itself needs more capacity.
        if ((used_count + 1) * 10 >= CAP * 7) {
            const int new_capacity = (state_count + 1) * 2 < CAP ? CAP : 2 * CAP;
            resize(new_capacity);
        }
        bool flag = 0;
            try {
                int temp = find(in.ID);
            } catch(std::out_of_range &e) {
                flag = 1;
            }
            if(!flag){
                throw std::invalid_argument("ID already exists");
            }
        const int start = static_cast<int>(hashie(in.ID) % CAP);
        int first_deleted = -1;
        for (int offset = 0; offset < CAP; ++offset) {
            const int slot = (start + offset) % CAP;
            if (tab[slot].ID == in.ID) {
                tab[slot].address = in.address;
                return;
            }
            if (tab[slot].ID == -2 && first_deleted == -1)
                first_deleted = slot;
            if (tab[slot].ID == -1) {
                const int put = first_deleted == -1 ? slot : first_deleted;
                if (first_deleted == -1) ++used_count;
                tab[put] = in;
                ++state_count;
                return;
            }
        }

        // A full probe cycle may still find a reusable tombstone.
        if (first_deleted != -1) {
            tab[first_deleted] = in;
            ++state_count;
            return;
        }
        resize(2 * CAP);
        Insert(in);
    }

    

    void Delete(int id) {
        const int slot = find_slot(id);
        if (slot == -1) throw std::out_of_range("Not Found");
        tab[slot].address = -1;
        tab[slot].ID = -2;
        --state_count;
    }

    void interchange(int first_id, int second_id) {
        const int first = find_slot(first_id);
        const int second = find_slot(second_id);
        if (first == -1 || second == -1)
            throw std::out_of_range("Locator entry missing during heap swap");
        std::swap(tab[first].address, tab[second].address);
    }
};
