/* ==========================================================================
   THE CLARITY CODE™ - INTERACTIVE LOGIC & ANIMATIONS
   Includes: GSAP animations, Testimonial Carousel, FAQ Accordion,
             Interactive Booking Scheduler, Blog Modal, and Form Validation
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

    /* --------------------------------------------------------------------------
       1. MOBILE NAVIGATION MENU
       -------------------------------------------------------------------------- */
    const mobileToggle = document.getElementById('mobile-toggle');
    const navMenu = document.getElementById('nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');

    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', () => {
            mobileToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        // Close menu when links are clicked
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileToggle.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }

    /* --------------------------------------------------------------------------
       2. STICKY CTA BAR DISPLAY
       -------------------------------------------------------------------------- */
    const stickyCta = document.getElementById('sticky-cta');
    const heroSection = document.getElementById('hero');

    window.addEventListener('scroll', () => {
        if (!stickyCta || !heroSection) return;
        
        const heroHeight = heroSection.offsetHeight;
        const scrollPosition = window.scrollY;

        // Show sticky bar after scrolling past 70% of hero section
        if (scrollPosition > heroHeight * 0.7) {
            stickyCta.classList.add('visible');
        } else {
            stickyCta.classList.remove('visible');
        }
    });

    /* --------------------------------------------------------------------------
       3. GSAP SCROLLTRIGGERS & ENTRANCE ANIMATIONS
       -------------------------------------------------------------------------- */
    // Register GSAP ScrollTrigger plugin safely
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
        gsap.registerPlugin(ScrollTrigger);

        // Hero Section entrance
        const tlHero = gsap.timeline({ defaults: { ease: 'power4.out', duration: 1 } });
        tlHero.from('.fade-in', {
            y: 40,
            opacity: 0,
            stagger: 0.15,
            delay: 0.2
        })
        .from('.hero-portrait', {
            scale: 0.95,
            opacity: 0,
            duration: 1.2
        }, '-=0.8')
        .from('.floating-badge', {
            y: 20,
            opacity: 0,
            stagger: 0.2,
            duration: 0.8
        }, '-=0.5');

        // Scroll animations for various blocks
        const animatedBlocks = document.querySelectorAll('.scroll-animate');
        animatedBlocks.forEach(block => {
            const animationType = block.getAttribute('data-animation');
            let fromVars = { opacity: 0, duration: 1, ease: 'power3.out' };

            if (animationType === 'fade-up') {
                fromVars.y = 50;
            } else if (animationType === 'fade-right') {
                fromVars.x = -60;
            } else if (animationType === 'fade-left') {
                fromVars.x = 60;
            }

            gsap.from(block, {
                ...fromVars,
                scrollTrigger: {
                    trigger: block,
                    start: 'top 85%',
                    toggleActions: 'play none none none'
                }
            });
        });

        // About Section Counter Numbers Animation
        const counterNums = document.querySelectorAll('.counter-num');
        counterNums.forEach(num => {
            const target = parseInt(num.getAttribute('data-target'), 10);
            gsap.to(num, {
                innerText: target,
                duration: 2.5,
                snap: { innerText: 1 },
                ease: 'power2.out',
                scrollTrigger: {
                    trigger: num,
                    start: 'top 90%',
                    toggleActions: 'play none none none'
                }
            });
        });

        // Timeline journey items incremental animations
        const timelineItems = document.querySelectorAll('.timeline-item');
        timelineItems.forEach((item, index) => {
            gsap.from(item.querySelector('.timeline-marker'), {
                scale: 0,
                opacity: 0,
                duration: 0.6,
                scrollTrigger: {
                    trigger: item,
                    start: 'top 80%'
                }
            });

            gsap.from(item.querySelector('.timeline-card'), {
                x: 30,
                opacity: 0,
                duration: 0.8,
                scrollTrigger: {
                    trigger: item,
                    start: 'top 80%'
                }
            });
        });
    }

    /* --------------------------------------------------------------------------
       4. TESTIMONIALS SLIDER (CAROUSEL)
       -------------------------------------------------------------------------- */
    const slides = document.querySelectorAll('.testimonial-slide');
    const dots = document.querySelectorAll('.slider-dots .dot');
    const btnPrev = document.getElementById('slider-prev');
    const btnNext = document.getElementById('slider-next');
    let currentSlide = 0;
    let slideInterval;

    if (slides.length > 0) {
        const updateSlider = (index) => {
            const slider = document.getElementById('testimonial-slider');
            if (!slider) return;

            // Constrain index
            if (index >= slides.length) currentSlide = 0;
            else if (index < 0) currentSlide = slides.length - 1;
            else currentSlide = index;

            // Shift slide container
            slider.style.transform = `translateX(-${currentSlide * 100}%)`;

            // Update classes
            slides.forEach((slide, idx) => {
                if (idx === currentSlide) slide.classList.add('active');
                else slide.classList.remove('active');
            });

            dots.forEach((dot, idx) => {
                if (idx === currentSlide) dot.classList.add('active');
                else dot.classList.remove('active');
            });
        };

        // Click next
        if (btnNext) {
            btnNext.addEventListener('click', () => {
                updateSlider(currentSlide + 1);
                resetAutoSlide();
            });
        }

        // Click prev
        if (btnPrev) {
            btnPrev.addEventListener('click', () => {
                updateSlider(currentSlide - 1);
                resetAutoSlide();
            });
        }

        // Click dots
        dots.forEach(dot => {
            dot.addEventListener('click', (e) => {
                const targetIdx = parseInt(e.target.getAttribute('data-index'), 10);
                updateSlider(targetIdx);
                resetAutoSlide();
            });
        });

        // Auto slide
        const startAutoSlide = () => {
            slideInterval = setInterval(() => {
                updateSlider(currentSlide + 1);
            }, 6000);
        };

        const resetAutoSlide = () => {
            clearInterval(slideInterval);
            startAutoSlide();
        };

        startAutoSlide();
    }

    /* --------------------------------------------------------------------------
       5. FAQ ACCORDION
       -------------------------------------------------------------------------- */
    const faqQuestions = document.querySelectorAll('.faq-question');

    faqQuestions.forEach(btn => {
        btn.addEventListener('click', () => {
            const faqItem = btn.parentElement;
            const answer = faqItem.querySelector('.faq-answer');
            const isActive = faqItem.classList.contains('active');

            // Close all other items
            document.querySelectorAll('.faq-item').forEach(item => {
                item.classList.remove('active');
                item.querySelector('.faq-answer').style.maxHeight = null;
            });

            // Toggle clicked item
            if (!isActive) {
                faqItem.classList.add('active');
                answer.style.maxHeight = answer.scrollHeight + "px";
            }
        });
    });

    /* --------------------------------------------------------------------------
       6. GENERAL MODAL TRIGGERS (OPEN / CLOSE)
       -------------------------------------------------------------------------- */
    const openModals = document.querySelectorAll('.open-booking-modal');
    const bookingModal = document.getElementById('booking-modal');
    const closeBookingBtn = document.querySelectorAll('.close-booking-modal, #close-booking-modal');
    
    // Video Modal
    const playIntroBtn = document.getElementById('play-intro-btn');
    const videoModal = document.getElementById('video-modal');
    const closeVideoBtn = document.getElementById('close-video-modal');

    // Open booking modal
    openModals.forEach(btn => {
        btn.addEventListener('click', () => {
            if (bookingModal) {
                bookingModal.classList.add('active');
                resetScheduler();
            }
        });
    });

    // Close booking modal
    closeBookingBtn.forEach(btn => {
        btn.addEventListener('click', () => {
            if (bookingModal) bookingModal.classList.remove('active');
        });
    });

    // Open video intro modal
    if (playIntroBtn && videoModal) {
        playIntroBtn.addEventListener('click', () => {
            videoModal.classList.add('active');
        });
    }

    if (closeVideoBtn && videoModal) {
        closeVideoBtn.addEventListener('click', () => {
            videoModal.classList.remove('active');
        });
    }

    // Close modals on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        const backdrop = modal.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        }
    });

    /* --------------------------------------------------------------------------
       7. INTERACTIVE SCHEDULER LOGIC (CALENDLY SIMULATION)
       -------------------------------------------------------------------------- */
    let selectedDate = null;
    let selectedTime = null;

    const calendarDays = document.querySelectorAll('.calendar-grid .day.available');
    const timeSlotList = document.getElementById('slot-list');
    const timeHintText = document.querySelector('.time-hint-text');
    const btnGotoDetails = document.getElementById('btn-goto-details');
    
    const stepDateTime = document.getElementById('step-date-time');
    const stepIntakeDetails = document.getElementById('step-intake-details');
    const stepSuccess = document.getElementById('step-success');

    const schedulerForm = document.getElementById('scheduler-form');

    // Calendar day selection
    calendarDays.forEach(day => {
        day.addEventListener('click', () => {
            // Remove selection class
            calendarDays.forEach(d => d.classList.remove('selected'));
            
            // Set current select
            day.classList.add('selected');
            selectedDate = day.getAttribute('data-date');
            
            // Show time slots
            if (timeSlotList && timeHintText) {
                timeHintText.classList.add('hidden');
                timeSlotList.classList.remove('hidden');
            }

            // Reset time slot selection
            selectedTime = null;
            document.querySelectorAll('.time-slot-btn').forEach(btn => btn.classList.remove('selected'));
            if (btnGotoDetails) btnGotoDetails.disabled = true;
        });
    });

    // Time slot selection
    const timeSlots = document.querySelectorAll('.time-slot-btn');
    timeSlots.forEach(slot => {
        slot.addEventListener('click', () => {
            timeSlots.forEach(s => s.classList.remove('selected'));
            slot.classList.add('selected');
            selectedTime = slot.getAttribute('data-time');

            if (btnGotoDetails && selectedDate) {
                btnGotoDetails.disabled = false;
            }
        });
    });

    // Go to step 2 (intake details)
    if (btnGotoDetails) {
        btnGotoDetails.addEventListener('click', () => {
            if (!selectedDate || !selectedTime) return;

            // Update step summaries
            const summaryDate = document.getElementById('summary-date');
            const summaryTime = document.getElementById('summary-time');
            
            if (summaryDate && summaryTime) {
                // Formatting readable date
                const dObj = new Date(selectedDate);
                const readableDate = dObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
                summaryDate.innerHTML = `<i class="fa-regular fa-calendar"></i> ${readableDate}`;
                summaryTime.innerHTML = `<i class="fa-regular fa-clock"></i> ${selectedTime} (IST)`;
            }

            if (stepDateTime && stepIntakeDetails) {
                stepDateTime.classList.add('hidden');
                stepIntakeDetails.classList.remove('hidden');
            }
        });
    }

    // Back to date time selection
    const btnBackToDateTime = document.getElementById('btn-back-to-datetime');
    if (btnBackToDateTime) {
        btnBackToDateTime.addEventListener('click', () => {
            if (stepDateTime && stepIntakeDetails) {
                stepIntakeDetails.classList.add('hidden');
                stepDateTime.classList.remove('hidden');
            }
        });
    }

    // Confirm Spot Form submit
    if (schedulerForm) {
        schedulerForm.addEventListener('click', (e) => {
            // Check if user clicked the button or triggered form
            // Event listener is on form, button is type submit. Let's register submit event
        });

        schedulerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Capture client details
            const clientName = document.getElementById('sched-name').value;
            
            // Format receipt
            const receiptDate = document.getElementById('receipt-date');
            const receiptTime = document.getElementById('receipt-time');
            if (receiptDate && receiptTime) {
                const dObj = new Date(selectedDate);
                receiptDate.textContent = dObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
                receiptTime.textContent = `${selectedTime} (IST)`;
            }

            // Transition to success screen
            if (stepIntakeDetails && stepSuccess) {
                stepIntakeDetails.classList.add('hidden');
                stepSuccess.classList.remove('hidden');
            }
        });
    }

    // Reset Scheduler
    const resetScheduler = () => {
        selectedDate = null;
        selectedTime = null;
        
        calendarDays.forEach(d => d.classList.remove('selected'));
        if (timeSlotList) timeSlotList.classList.add('hidden');
        if (timeHintText) timeHintText.classList.remove('hidden');
        if (btnGotoDetails) btnGotoDetails.disabled = true;

        if (stepDateTime) stepDateTime.classList.remove('hidden');
        if (stepIntakeDetails) stepIntakeDetails.classList.add('hidden');
        if (stepSuccess) stepSuccess.classList.add('hidden');

        if (schedulerForm) schedulerForm.reset();
    };

    /* --------------------------------------------------------------------------
       8. BLOG DATABASE & READER MODAL RENDERING
       -------------------------------------------------------------------------- */
    const blogArticles = {
        'article-1': {
            tag: 'Overthinking',
            title: 'How to Quiet the Mind: The 5-Minute Cognitive Reset',
            date: 'June 18, 2026',
            readTime: '5 min read',
            content: `
                <p>For young professionals, overthinking isn't just a minor habit—it is a cognitive tax. We spend hours analyzing emails, projecting worst-case outcomes of stakeholder meetings, and reconsidering choices that were already made. This drains our mental energy before actual execution begins.</p>
                
                <h4>Why Your Brain Overthinks</h4>
                <p>Under stress, your amygdala triggers threat-detection sequences. It treats career ambiguity (e.g. "what if my lead doesn't like my proposal?") as a physical predator. To solve this, your prefrontal cortex spins up infinite loops to find a 'perfect' resolution, leading to analysis paralysis.</p>

                <h4>The 3-Step Somali Reset Protocol</h4>
                <p>When you feel your mind racing, apply this somatic framework to shut down the survival alarm system:</p>
                <ul>
                    <li><strong>Ground the body (2 mins):</strong> Place your feet firmly on the ground. Scan for physical tension in your jaw, neck, and shoulders. Exhale slowly, making the exhalation twice as long as the inhalation.</li>
                    <li><strong>Fact vs. Projection Audit (2 mins):</strong> Open a notepad and draw two columns. Write down exact physical facts in the left column (e.g. "My manager rescheduled our 1-on-1"). Write down your projections in the right column ("My manager is going to fire me"). Label the projections as 'Unverified Theories'.</li>
                    <li><strong>Commit to a Micro-Decision (1 min):</strong> Pick a task that takes less than 3 minutes (e.g., replying to a quick slack message or opening a doc draft) and perform it immediately. Action is the biological cure for anxiety.</li>
                </ul>

                <h4>Implementing Daily Rules</h4>
                <p>Set boundaries for your thinking. Allocate 15 minutes of "Worry Time" at 5:00 PM. If a worrying thought arises at 11:00 AM, write it down and table it for the designated period. You will find that by 5:00 PM, 90% of the items have lost their emotional charge.</p>
            `
        },
        'article-2': {
            tag: 'Habits',
            title: 'The Science of Habit Stacking: Building Lasting Discipline',
            date: 'June 12, 2026',
            readTime: '4 min read',
            content: `
                <p>Many young professionals believe consistency is a matter of willpower. They expect themselves to wake up at 5:00 AM, go to the gym, drink green juice, and read 20 pages through sheer grit. But grit is a exhaustible fuel. The real secret to lifetime consistency is habit engineering.</p>
                
                <h4>The Neurology of the Habit Loop</h4>
                <p>Habits are formed by the basal ganglia. The brain seeks to automate behaviors to conserve energy. A habit requires a cue (trigger), a routine (action), and a reward (dopamine release). If any of these are missing, the habit collapses within days.</p>

                <h4>The Habit Stacking Framework</h4>
                <p>The easiest way to install a new habit is to anchor it to an established, automatic daily routine. The formula is: <strong>After [Current Habit], I will [New Habit].</strong></p>
                
                <h4>Practical Examples for Corporate Professionals:</h4>
                <ul>
                    <li><strong>For Career Growth:</strong> "After I open my morning laptop and drink my first sip of coffee, I will write down my 3 Aligned Focus items for the day."</li>
                    <li><strong>For Stress Management:</strong> "After I close my laptop lid at the end of the workday, I will close my eyes and take 5 deep somatic breaths to shift states."</li>
                    <li><strong>For Physical Health:</strong> "After I brush my teeth at night, I will lay out my workout clothing on the chair for the next morning."</li>
                </ul>

                <h4>Reducing Friction</h4>
                <p>Make the cue visible and the action simple. If you want to read more, put the book on your pillow. If you want to stop checking social media at work, block the site on your browser. Control your environment so discipline becomes the path of least resistance.</p>
            `
        },
        'article-3': {
            tag: 'Emotional Intelligence',
            title: 'Corporate Boundaries: Say \'No\' and Gain Respect',
            date: 'June 05, 2026',
            readTime: '6 min read',
            content: `
                <p>Many young professionals suffer from people-pleasing tendencies. They take on late-night assignments, say yes to ambiguous goals, and allow managers to cross boundaries out of fear of looking lazy. Ironically, this behavior usually leads to burnout, low performance, and a lack of respect from senior leadership.</p>
                
                <h4>The Assertiveness Paradox</h4>
                <p>High performers are respected not because they say yes to everything, but because they protect their focus and execute their core tasks with excellence. A professional who sets boundaries communicates high agency and executive maturity.</p>

                <h4>How to Decline Work Diplomatically (Scripts)</h4>
                <p>Never say "I don't want to do this" or "I am too busy". Instead, use priority mapping scripts:</p>
                <ul>
                    <li><strong>When a manager dumps an ad-hoc project:</strong> "I’d love to help with this. Currently, my main priorities are Tasks A and B. To take this on, should we deprioritize one of those, or push back the timeline of this new request?"</li>
                    <li><strong>When asked to work over the weekend:</strong> "I want to make sure this deliverable is top quality. I am offline this weekend to recharge, but I will tackle this first thing Monday morning to have it ready for review by noon."</li>
                    <li><strong>When meetings overload your calendar:</strong> "I see we have a sync scheduled. To protect my coding/design time, can I provide my updates via email, or is there a specific agenda item that requires my active input?"</li>
                </ul>

                <h4>Stabilizing Your Nervous System</h4>
                <p>Setting boundaries triggers short-term guilt. Understand that this guilt is just a sign that you are breaking old, submissive habits. Sit with the discomfort, remind yourself of your long-term career mission, and watch how your team adjusts to your new boundaries.</p>
            `
        }
    };

    const blogModal = document.getElementById('blog-modal');
    const blogReaderBody = document.getElementById('blog-reader-body');
    const closeBlogBtn = document.getElementById('close-blog-modal');
    const blogCards = document.querySelectorAll('.blog-card');

    if (blogCards.length > 0 && blogModal && blogReaderBody) {
        blogCards.forEach(card => {
            const triggerBtn = card.querySelector('.read-blog-trigger');
            const handler = () => {
                const articleId = card.getAttribute('data-article-id');
                const article = blogArticles[articleId];
                
                if (article) {
                    // Populate modal content
                    blogReaderBody.innerHTML = `
                        <div class="blog-article-full">
                            <span class="blog-tag">${article.tag}</span>
                            <h2>${article.title}</h2>
                            <div class="blog-meta-bar">
                                <span><i class="fa-regular fa-calendar"></i> ${article.date}</span>
                                <span><i class="fa-regular fa-clock"></i> ${article.readTime}</span>
                                <span>By Komal Sharma</span>
                            </div>
                            <div class="blog-body-text">
                                ${article.content}
                            </div>
                            <div style="margin-top: 3rem; text-align: center; border-top: 1px solid var(--border-glass); padding-top: 2rem;">
                                <h4 style="font-family: var(--font-heading); margin-bottom: 1rem;">Ready to break your bottlenecks?</h4>
                                <button class="btn btn-gold open-booking-modal" id="modal-blog-cta">Book A Free Clarity Call</button>
                            </div>
                        </div>
                    `;

                    // Show modal
                    blogModal.classList.add('active');

                    // Bind the CTA inside modal
                    const blogCta = document.getElementById('modal-blog-cta');
                    if (blogCta) {
                        blogCta.addEventListener('click', () => {
                            blogModal.classList.remove('active');
                            if (bookingModal) {
                                bookingModal.classList.add('active');
                                resetScheduler();
                            }
                        });
                    }
                }
            };

            if (triggerBtn) triggerBtn.addEventListener('click', handler);
            card.addEventListener('click', (e) => {
                // Ensure clicks on buttons don't double fire, but let card clicks open as well
                if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
                    handler();
                }
            });
        });
    }

    if (closeBlogBtn && blogModal) {
        closeBlogBtn.addEventListener('click', () => {
            blogModal.classList.remove('active');
        });
    }

    /* --------------------------------------------------------------------------
       9. FORM VALIDATIONS & SIMULATED SUBMISSIONS
       -------------------------------------------------------------------------- */
    // Contact Form Handler
    const contactForm = document.getElementById('contact-form');
    const contactSuccess = document.getElementById('form-success');

    if (contactForm && contactSuccess) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();

            // Simulate server request
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending...';

            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                
                // Show success message
                contactSuccess.style.display = 'flex';
                contactForm.reset();

                // Fade out success message after 5 seconds
                setTimeout(() => {
                    contactSuccess.style.display = 'none';
                }, 5000);
            }, 1500);
        });
    }

    // Newsletter Form Handler
    const newsletterForm = document.getElementById('newsletter-form');
    const newsletterSuccess = document.getElementById('newsletter-success');

    if (newsletterForm && newsletterSuccess) {
        newsletterForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const inputField = newsletterForm.querySelector('input');
            const submitBtn = newsletterForm.querySelector('button');
            
            submitBtn.disabled = true;
            inputField.disabled = true;

            setTimeout(() => {
                submitBtn.disabled = false;
                inputField.disabled = false;
                
                // Show success message
                newsletterSuccess.style.display = 'flex';
                newsletterForm.reset();

                // Hide success message after 4 seconds
                setTimeout(() => {
                    newsletterSuccess.style.display = 'none';
                }, 4000);
            }, 1200);
        });
    }
});
