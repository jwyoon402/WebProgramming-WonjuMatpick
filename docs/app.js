

let currentUser = JSON.parse(

    localStorage.getItem("currentUser")

) || null;



let reviews = JSON.parse(

    localStorage.getItem("reviews")

) || [];



let selectedStar = 0;



const users = [

    { id: 1, name: "맛집탐험가" },

    { id: 2, name: "원주먹방러" },

    { id: 3, name: "오늘뭐먹지" },

    { id: 4, name: "푸드러버" }

];



let following = JSON.parse(

    localStorage.getItem("following")

) || [];


function showPage(pageName) {



    const pages = document.querySelectorAll(".page");

    

    pages.forEach(function(page) {

        page.classList.remove("active");

    });

    

    document.getElementById(pageName)

        .classList.add("active");

    

    if (pageName === "mypage") {

        updateMyPage();

    }

    

    if (pageName === "following") {

        showFollowing();

    }

    

    if (pageName === "review") {

        showReviews();

    }

}



function selectStar(number) {

    

    selectedStar = number;

    

    const stars = document.querySelectorAll(

        "#starBox button"

    );

    

    stars.forEach(function(star, index) {

        if (index < number) {

            star.classList.add("selected");

        } else {

            star.classList.remove("selected");

        }

    });

}



function addReview() {

    

    if (!currentUser) {

        alert("로그인 후 리뷰를 작성해주세요.");

        return;

    }

    

    const content = document.getElementById(

        "reviewText"

    ).value.trim();

    

    if (selectedStar === 0) {

        alert("별점을 선택해주세요.");

        return;

    }

    

    if (content === "") {

        alert("리뷰 내용을 작성해주세요.");

        return;

    }

    

    const newReview = {

        nickname: currentUser.nickname,

        star: selectedStar,

        content: content

    };

    
    reviews.push(newReview);

    

    localStorage.setItem(

        "reviews",

        JSON.stringify(reviews)

    );

    

    document.getElementById("reviewText").value = "";

    

    selectedStar = 0;

    

    document.querySelectorAll(

        "#starBox button"

    ).forEach(function(star) {

        star.classList.remove("selected");

    });

    

    showReviews();

    alert("리뷰가 등록되었습니다.");

}



function showReviews() {

    const list = document.getElementById(

        "reviewList"

    );

    

    list.innerHTML = "";

    

    if (reviews.length === 0) {

        list.textContent = "아직 등록된 리뷰가 없습니다.";

        return;

    }

 

    reviews.forEach(function(review) {

        const item = document.createElement("div");

        item.className = "review-item";

        const name = document.createElement("b");

        name.textContent = review.nickname;

        const rating = document.createElement("p");

        rating.textContent = "★".repeat(review.star);

        const content = document.createElement("p");

        content.textContent = review.content;

        item.append(name, rating, content);

        list.appendChild(item);

    });

}


function login() {

    

    const id = document.getElementById(

        "userId"

    ).value.trim();

    

    const pw = document.getElementById(

        "userPw"

    ).value;

    

    if (id === "" || pw === "") {

        alert("아이디와 비밀번호를 입력해주세요.");

        return;

    }

    

    currentUser = {

        id: id,

        nickname: id

    };

    

    localStorage.setItem(

        "currentUser",

        JSON.stringify(currentUser)

    );

    

    document.getElementById(

        "loginMessage"

    ).textContent = "로그인되었습니다!";

    alert("로그인 성공!");

    updateMyPage();

}



function logout() {

    

    currentUser = null;

    localStorage.removeItem("currentUser");

    

    updateMyPage();

    alert("로그아웃되었습니다.");

    showPage("login");

}

//룰렛

const menus = [

    "한식 🍚",

    "중식 🍜",

    "일식 🍣",

    "양식 🍕",

    "분식 🍢",

    "치킨 🍗"

];



function spinRoulette() {

    const wheel = document.getElementById("wheel");

    const result = document.getElementById(

        "rouletteResult"

    );

 

    if (wheel.classList.contains("spinning")) {

        return;

    }

    

    wheel.classList.remove("spinning");

    

    void wheel.offsetWidth;

    

    wheel.classList.add("spinning");

    

    const randomNumber = Math.floor(

        Math.random() * menus.length

    );

    

    setTimeout(function() {

        result.textContent =

            "오늘의 추천 메뉴: " +

            menus[randomNumber];

        wheel.classList.remove("spinning");

    }, 2000);

}


function updateMyPage() {

    

    if (!currentUser) {

        document.getElementById(

            "myNickname"

        ).textContent = "로그인이 필요합니다.";

        document.getElementById(

            "myId"

        ).textContent = "아이디: -";

        document.getElementById(

            "myReviewCount"

        ).textContent = "0";

        document.getElementById(

            "myFollowingCount"

        ).textContent = "0";

        document.getElementById(

            "myReviewList"

        ).textContent = "";

        return;

    }

    

    document.getElementById(

        "myNickname"

    ).textContent = currentUser.nickname;

    document.getElementById(

        "myId"

    ).textContent = "아이디: " + currentUser.id;



    const myReviews = reviews.filter(

        function(review) {

            return review.nickname === currentUser.nickname;

        }

    );

    

    document.getElementById(

        "myReviewCount"

    ).textContent = myReviews.length;

    

    document.getElementById(

        "myFollowingCount"

    ).textContent = following.length;



    const list = document.getElementById(

        "myReviewList"

    );

    list.innerHTML = "";

    myReviews.forEach(function(review) {

        const item = document.createElement("div");

        item.className = "review-item";

        const rating = document.createElement("p");

        rating.textContent = "★".repeat(review.star);

        const content = document.createElement("p");

        content.textContent = review.content;

        item.append(rating, content);

        list.appendChild(item);

    });

}


function showFollowing() {

    const list = document.getElementById(

        "followingList"

    );
    
    list.innerHTML = "";

    users.forEach(function(user) {

        const item = document.createElement("div");

        item.className = "follow-item";

        const name = document.createElement("span");

        name.textContent = "👤 " + user.name;

        const button = document.createElement("button");

        button.className = "follow-btn";

        const isFollowing = following.includes(user.id);

        button.textContent = isFollowing

            ? "팔로잉"

            : "팔로우";

        if (isFollowing) {

            button.classList.add("followed");

        }

        button.onclick = function() {

            toggleFollow(user.id);

        };

        item.append(name, button);

        list.appendChild(item);

    });

}

function toggleFollow(userId) {

    if (following.includes(userId)) {

        following = following.filter(

            function(id) {

                return id !== userId;

            }

        );

    } else {

        following.push(userId);

    }

    localStorage.setItem(

        "following",

        JSON.stringify(following)

    );

    showFollowing();

    updateMyPage();

}

showPage("review");

showReviews();

updateMyPage();

showFollowing();