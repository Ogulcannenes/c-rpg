import unittest
from unittest.mock import patch

from concept_checker import check_cpp_concept
from curriculum import CURRICULUM
from mission_contracts import BOSSES, FIXES, PRACTICE
import server


VALID_CONCEPT_EXAMPLES = {
    "output_main": '#include <iostream>\nint main(){std::cout << "Hello";} ',
    "typed_variables": '#include <iostream>\n#include <string>\nint main(){int paws=4;std::string name="Pati";std::cout<<name<<" "<<paws;}',
    "input_output": '#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n;}',
    "input_arithmetic": '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b*2;}',
    "input_branch": '#include <iostream>\nint main(){int n;std::cin>>n;if(n>=50)std::cout<<"yes";else std::cout<<"no";}',
    "input_loop": '#include <iostream>\nint main(){int n;std::cin>>n;int sum=0;for(int i=1;i<=n;++i)sum+=i;std::cout<<sum;}',
    "function_output": '#include <iostream>\nint twice(int n){return n*2;}int main(){int n;std::cin>>n;std::cout<<twice(n);}',
    "vector_iteration": '#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(auto& x:v)std::cin>>x;int s=0;for(int x:v)s+=x;std::cout<<s;}',
    "string_output": '#include <iostream>\n#include <string>\nint main(){std::string name;std::getline(std::cin,name);std::cout<<"Hi "<<name;}',
    "reference_alias": '#include <iostream>\nint main(){int n;std::cin>>n;int& alias=n;++alias;std::cout<<n;}',
    "struct_member": '#include <iostream>\n#include <string>\nstruct Cat{std::string name;int age;};int main(){std::string n;int a;std::cin>>n>>a;Cat c{n,a};std::cout<<c.name<<" "<<c.age;}',
    "class_method": '#include <iostream>\nclass Hero{int power;public:Hero(int p):power(p){}int boosted(){return power+2;}};int main(){int p;std::cin>>p;Hero h(p);std::cout<<h.boosted();}',
    "stl_sort": '#include <iostream>\n#include <vector>\n#include <algorithm>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(auto& x:v)std::cin>>x;std::sort(v.begin(),v.end());for(int x:v)std::cout<<x<<" ";}',
    "file_exception": '#include <iostream>\n#include <fstream>\n#include <stdexcept>\nint main(){int n;std::cin>>n;try{std::ofstream out("save.txt");if(!out)throw std::runtime_error("no file");out<<n;out.close();std::ifstream in("save.txt");int saved;in>>saved;std::cout<<saved;}catch(...){std::cout<<"error";}}',
    "integrated_project": '#include <iostream>\n#include <string>\nstd::string rankFor(int n){if(n>=20)return "Gold";return "Silver";}int main(){std::string name;int count;std::cin>>name>>count;int total=0;for(int i=0;i<count;++i){int x;std::cin>>x;if(x>3)total+=x;}std::cout<<name<<" "<<rankFor(total);}',
}

PRACTICE_SOLUTIONS = [
    '#include <iostream>\nint main(){std::cout<<"C++ ADVENTURE\\nMerhaba, C++!\\nMacera başlıyor!";}',
    '#include <iostream>\n#include <string>\nint main(){std::string name="Pati";int paws=4;std::cout<<name<<" "<<paws;}',
    '#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2;}',
    '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+2*b;}',
    '#include <iostream>\nint main(){int score;std::cin>>score;if(score>=50)std::cout<<"Gecti";else std::cout<<"Tekrar";}',
    '#include <iostream>\nint main(){int n;std::cin>>n;for(int i=1;i<=n;++i){if(i>1)std::cout<<" ";std::cout<<i;}}',
    '#include <iostream>\nint ikiKat(int n){return n*2;}int main(){int n;std::cin>>n;std::cout<<ikiKat(n);}',
    '#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int& x:v)std::cin>>x;int sum=0;for(int x:v)sum+=x;std::cout<<sum;}',
    '#include <iostream>\n#include <string>\nint main(){std::string name;std::getline(std::cin,name);std::cout<<"Merhaba "<<name;}',
    '#include <iostream>\nint main(){int value;std::cin>>value;int& alias=value;++alias;std::cout<<value;}',
    '#include <iostream>\n#include <string>\nstruct Kedi{std::string ad;int yas;};int main(){std::string ad;int yas;std::cin>>ad>>yas;Kedi k{ad,yas};std::cout<<k.ad<<" "<<k.yas;}',
    '#include <iostream>\nclass Hero{int power;public:Hero(int p):power(p){}int boosted(){return power+2;}};int main(){int p;std::cin>>p;Hero h(p);std::cout<<h.boosted();}',
    '#include <iostream>\n#include <vector>\n#include <algorithm>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int& x:v)std::cin>>x;std::sort(v.begin(),v.end());for(int x:v)std::cout<<x<<" ";}',
    '#include <iostream>\n#include <fstream>\n#include <stdexcept>\n#include <string>\nint main(){std::string n;int xp;std::cin>>n>>xp;try{std::ofstream o("save.txt");if(!o)throw std::runtime_error("io");o<<n<<" "<<xp;o.close();std::ifstream i("save.txt");std::string s;int v;i>>s>>v;std::cout<<s<<" "<<v;}catch(...){std::cout<<"error";}}',
    '#include <iostream>\n#include <string>\nstd::string rankFor(int n){return n>=50?"Gold":"Silver";}int main(){std::string name;int count;std::cin>>name>>count;int total=0;for(int i=0;i<count;++i){int p;std::cin>>p;if(p>=25)total+=p+5;else total+=p;}std::cout<<name<<" "<<total<<" "<<rankFor(total);}',
]

BOSS_SOLUTIONS = [
    '#include <iostream>\nint main(){std::cout<<"=== KEDI GUILD ===\\nMerhaba, gezgin!\\nKodun gücü seninle!";}',
    '#include <iostream>\n#include <string>\nint main(){std::string name="Luna";int potions=3;double strength=2.5;std::cout<<name<<" "<<potions<<" "<<strength;}',
    '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n"<<a*b;}',
    '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<(a+b)*(a-b);}',
    '#include <iostream>\nint main(){int p;std::cin>>p;if(p>=80)std::cout<<"Usta";else if(p>=50)std::cout<<"Gezgin";else std::cout<<"Cirak";}',
    '#include <iostream>\nint main(){int n;std::cin>>n;int sum=0;for(int i=2;i<=n;i+=2)sum+=i;std::cout<<sum;}',
    '#include <iostream>\nint gorevPuani(int a,int b,int c){return a+2*b-c;}int main(){int a,b,c;std::cin>>a>>b>>c;std::cout<<gorevPuani(a,b,c);}',
    '#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int& x:v)std::cin>>x;int best=v[0];for(int x:v)if(x>best)best=x;std::cout<<best;}',
    '#include <iostream>\n#include <string>\nint main(){std::string a,b;std::cin>>a>>b;std::string full=a+" "+b;std::cout<<full<<" "<<full.size();}',
    '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;int& left=a;int& right=b;int temp=left;left=right;right=temp;std::cout<<a<<" "<<b;}',
    '#include <iostream>\n#include <string>\nstruct Quest{std::string name;int xp;bool done;};int main(){std::string n;int xp,done;std::cin>>n>>xp>>done;Quest q{n,xp,done==1};std::cout<<q.name<<" "<<q.xp<<" "<<(q.done?"Tamam":"Acik");}',
    '#include <iostream>\nclass Hero{int power;public:Hero(int p):power(p){}int train(int bonus){return power+bonus;}};int main(){int p,b;std::cin>>p>>b;Hero h(p);std::cout<<h.train(b);}',
    '#include <iostream>\n#include <vector>\n#include <algorithm>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int& x:v)std::cin>>x;std::sort(v.begin(),v.end());std::cout<<v.front()<<" "<<v.back();}',
    '#include <iostream>\n#include <fstream>\n#include <stdexcept>\nint main(){int n;std::cin>>n;try{std::ofstream o("scores.txt");if(!o)throw std::runtime_error("io");for(int i=0;i<n;++i){int x;std::cin>>x;o<<x<<" ";}o.close();std::ifstream in("scores.txt");if(!in)throw std::runtime_error("io");int sum=0,x;while(in>>x)sum+=x;std::cout<<sum;}catch(...){std::cout<<"error";}}',
    '#include <iostream>\n#include <string>\nstd::string rankFor(int xp){if(xp>=70)return "Gold";if(xp>=20)return "Silver";return "Bronze";}int main(){std::string name;int xp,n;std::cin>>name>>xp>>n;for(int i=0;i<n;++i){int reward;std::cin>>reward;if(reward>=30)xp+=reward+5;else xp+=reward;}std::cout<<name<<" "<<xp<<" "<<rankFor(xp);}',
]

FIX_SOLUTIONS = [
    '#include <iostream>\nint main(){std::cout<<"C++ ADVENTURE\\nMerhaba, C++!\\nMacera başlıyor!";}',
    '#include <iostream>\n#include <string>\nint main(){int yas=7;std::string ad="Mırmır";std::cout<<ad<<" "<<yas;}',
    '#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2;}',
    '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<(a+b)*2;}',
    '#include <iostream>\nint main(){int puan;std::cin>>puan;if(puan>=50)std::cout<<"Gecti";else std::cout<<"Tekrar";}',
    '#include <iostream>\nint main(){int n;std::cin>>n;for(int i=1;i<=n;++i){if(i>1)std::cout<<" ";std::cout<<i;}}',
    '#include <iostream>\nint ikiKat(int x){return x*2;}int main(){int n;std::cin>>n;std::cout<<ikiKat(n);}',
    '#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int& x:v)std::cin>>x;int s=0;for(int x:v)s+=x;std::cout<<s;}',
    '#include <iostream>\n#include <string>\nint main(){std::string name;std::cin>>name;std::cout<<"Merhaba "<<name;}',
    '#include <iostream>\nint main(){int value;std::cin>>value;int& ref=value;++ref;std::cout<<value;}',
    '#include <iostream>\n#include <string>\nstruct Kedi{std::string ad;int yas;};int main(){std::string ad;int yas;std::cin>>ad>>yas;Kedi k{ad,yas};std::cout<<k.ad<<" "<<k.yas;}',
    '#include <iostream>\nclass Hero{int power;public:Hero(int p):power(p){}int boosted(){return power+2;}};int main(){int p;std::cin>>p;Hero h(p);std::cout<<h.boosted();}',
    '#include <iostream>\n#include <vector>\n#include <algorithm>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int& x:v)std::cin>>x;std::sort(v.begin(),v.end());for(int x:v)std::cout<<x<<" ";}',
    '#include <iostream>\n#include <fstream>\n#include <stdexcept>\n#include <string>\nint main(){std::string n;int xp;std::cin>>n>>xp;try{std::ofstream o("save.txt");if(!o)throw std::runtime_error("io");o<<n<<" "<<xp;o.close();std::ifstream i("save.txt");std::string s;int v;i>>s>>v;std::cout<<s<<" "<<v;}catch(...){std::cout<<"error";}}',
    '#include <iostream>\n#include <string>\nint main(){std::string name;int xp;std::cin>>name>>xp;std::cout<<name<<" "<<xp;}',
]


class MissionContractTests(unittest.TestCase):
    def test_ast_concept_rules_accept_meaningful_cpp_structures(self):
        for rule, source in VALID_CONCEPT_EXAMPLES.items():
            with self.subTest(rule=rule):
                result = check_cpp_concept(source, rule, "tr")
                self.assertTrue(result["passed"], result)
                russian = check_cpp_concept(source, rule, "ru")
                self.assertTrue(russian["passed"], russian)
                self.assertNotEqual(result["label"], russian["label"])

    def test_comments_strings_unused_variables_and_fixed_output_do_not_satisfy_rules(self):
        examples = {
            "typed_variables": '#include <iostream>\n#include <string>\nint main(){int unused=4;std::string note="Pati 4";std::cout<<"Pati 4";}',
            "input_branch": '#include <iostream>\nint main(){int n;std::cin>>n;/* if(n) */std::cout<<"yes";}',
            "vector_iteration": '#include <iostream>\nint main(){std::cout<<"std::vector for";}',
            "function_output": '#include <iostream>\nint main(){std::cout<<"twice(4) return";}',
            "reference_alias": '#include <iostream>\nint main(){int n=4;std::cout<<"int& ref"<<n;}',
        }
        for rule, source in examples.items():
            with self.subTest(rule=rule):
                self.assertFalse(check_cpp_concept(source, rule)["passed"])

    def test_structural_fallback_ignores_comment_and_literal_decoys(self):
        with patch("concept_checker._main_ast", return_value=None):
            for rule, source in VALID_CONCEPT_EXAMPLES.items():
                with self.subTest(valid_rule=rule):
                    self.assertTrue(check_cpp_concept(source, rule)["passed"])
            fake_branch = '#include <iostream>\nint main(){int n;std::cin>>n; // if else\nstd::cout<<"if else";}'
            fake_vector = '#include <iostream>\nint main(){std::cout<<"std::vector for";}'
            self.assertFalse(check_cpp_concept(fake_branch, "input_branch")["passed"])
            self.assertFalse(check_cpp_concept(fake_vector, "vector_iteration")["passed"])

    def test_all_reauthored_code_and_boss_cases_use_real_gpp(self):
        for category, specs, solutions in (("fix", FIXES, FIX_SOLUTIONS), ("practice", PRACTICE, PRACTICE_SOLUTIONS), ("boss", BOSSES, BOSS_SOLUTIONS)):
            for index, (spec, source) in enumerate(zip(specs, solutions), 1):
                with self.subTest(category=category, chapter=index):
                    concept = check_cpp_concept(source, spec["rule"], "tr")
                    self.assertTrue(concept["passed"], concept)
                    for case_index, case in enumerate(spec["tests"], 1):
                        result = server.compile_and_run(source, case["input"])
                        self.assertTrue(result["ok"], f"{category} c{index:02}, case {case_index}: {result}")
                        self.assertEqual(result["stdout"].strip(), case["expected"].strip(), f"{category} c{index:02}, case {case_index}")

    def test_all_code_missions_have_rules_bilingual_content_and_distinct_bosses(self):
        # Contracts cover the 20 core chapters; the modern track (c21-c24) has its own tests.
        self.assertEqual((len(CURRICULUM), sum(len(c["tasks"]) for c in CURRICULUM)), (24, 192))
        self.assertEqual((len(PRACTICE), len(FIXES), len(BOSSES)), (20, 20, 20))
        for chapter, fix, practice, boss in zip(CURRICULUM, FIXES, PRACTICE, BOSSES):
            with self.subTest(chapter=chapter["id"]):
                for task, spec in zip([chapter["tasks"][4], chapter["tasks"][6], chapter["tasks"][7]], (fix, practice, boss)):
                    self.assertEqual(task["concept_rule"], spec["rule"])
                    self.assertTrue(task["concept_criteria"]["tr"])
                    self.assertTrue(task["concept_criteria"]["ru"])
                    self.assertGreaterEqual(len(task["tests"]), 1)
                exercise, final_boss = chapter["tasks"][6:8]
                self.assertNotEqual(exercise["prompt"]["tr"], final_boss["prompt"]["tr"])
                self.assertNotEqual(exercise["starter"], final_boss["starter"])
                self.assertNotEqual(exercise["tests"], final_boss["tests"])


if __name__ == "__main__":
    unittest.main()
