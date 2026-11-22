#include <iostream>
#include <vector>
#include <stdexcept>
#include <string>
#include <algorithm>

#include "locator_for_structure_A.cpp"
#include "../../app/ITriageQueue.h"

#ifdef D5_COUNT_COMPARISONS
extern unsigned long long d5_comparisons;
#define D5_COMPARE(expression) (++d5_comparisons, (expression))
#else
#define D5_COMPARE(expression) (expression)
#endif

class Min_Heap : public ITriageQueue {
private:
    LookUp table;
    std::vector<Patient> Heap;
    int count = 0;

    static bool comes_before(const Patient& a, const Patient& b) {
        if (a.priority_key != b.priority_key)
            return D5_COMPARE(a.priority_key < b.priority_key);
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        return a.id < b.id;
    }

    void Sift_Down(int index) {
         while(true) {
         const int left = 2*index +1;
         const int right = 2*index+2;
        int smallest = index ;
        if (left<count && comes_before(Heap[left],Heap[smallest])) {
            smallest = left;
        }

        if (right<count && comes_before(Heap[right],Heap[smallest]) {
            smallest = right;
        }
       if (smallest == index){
           return ;
       }
         std::swap(Heap[index],Heap[smallest]);
         table.interchange(Heap[index].id,Heap[smallest].id);
           index= smallest;
         }
    }



    void heapify() {
        for (int i = count / 2 - 1; i >= 0; i--) {
            Sift_Down(i);
        }
    }

    void Insertify(int index) {
        while (index > 0) {
            const int parent = (index-1)/2;
            if(!comes_before(Heap[index],Heap[parent]))
            {
            return;
        }
            

            std::swap(Heap[parent], Heap[index]);

            table.interchange(
                Heap[index].id,
                Heap[parent].id
            );

            index = parent;
        }
    }

public:
    Min_Heap() = default;

    Min_Heap(const std::vector<Patient>& patients) {
        build_heap(patients);
    }

    void build_heap(
        const std::vector<Patient>& patients
    ) override {
        table = LookUp();
        Heap = patients;
        count = static_cast<int>(Heap.size());

        for (int i = 0; i < count; i++) {
            table.Insert(twin(Heap[i].id, i));
        }

        heapify();
    }

    void insert(const Patient& patient) override {
        Heap.push_back(patient);
        count = static_cast<int>(Heap.size());

        table.Insert(twin(patient.id, count - 1));

        Insertify(count - 1);
    }

    Patient peek() {
        if (count == 0) {
            throw std::out_of_range(
                "No patients are currently waiting for triage."
            );
        }

        return Heap[0];
    }

    Patient extract_min() override {
        if (count == 0) {
            throw std::out_of_range(
                "No patients are currently waiting for triage."
            );
        }

        Patient minimum = Heap[0];

        std::swap(Heap[0], Heap[count - 1]);

        table.interchange(
            Heap[count - 1].id,
            Heap[0].id
        );

        table.Delete(Heap[count - 1].id);

        Heap.pop_back();
        count--;

        Sift_Down(0);

        return minimum;
    }

    void delete_patient(int id) override {
        int index = table.find(id);

        std::swap(Heap[index], Heap[count - 1]);

        table.interchange(
            Heap[index].id,
            Heap[count - 1].id
        );

        table.Delete(Heap[count - 1].id);

        Heap.pop_back();
        count--;

        if (index < count) {
            if (index > 0 && comes_before(Heap[index], Heap[(index - 1) / 2]))
                Insertify(index);
            else
                Sift_Down(index);
        }
    }

    void decrease_key(int id, long long new_key) override {
        int index = table.find(id);

        if (new_key > Heap[index].priority_key)
            throw std::invalid_argument("decrease_key cannot increase the key");

        Heap[index].priority_key = new_key;

        Insertify(index);
    }
};

 
#undef D5_COMPARE

